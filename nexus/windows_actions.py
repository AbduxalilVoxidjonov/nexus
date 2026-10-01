"""Windows tizim amallari — `MacOSController` bilan bir xil interfeys.

AppleScript o'rniga: ctypes (user32 — media/ovoz klavishlari, qulflash, faol oyna), psutil,
`os.startfile` va konsol oynasiz PowerShell (`-NoProfile -NonInteractive`). Hali Windows
ekvivalenti yozilmagan toollar `SUPPORTED_TOOLS` dan tashqarida — registry ularni Gemini'ga
umuman e'lon qilmaydi, shuning uchun model ularni chaqirmaydi.
"""

from __future__ import annotations

import asyncio
import ctypes
import logging
import os
import platform
import shlex
import shutil
import subprocess
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

from nexus.config import settings
from nexus.macos_actions import (
    APP_CACHE_TTL,
    MAX_OUTPUT_CHARS,
    CommandGuard,
    MacOSController,
    Result,
    Verdict,
    _clamp,
    _fmt_uptime,
    _summarize_info,
    _truncate,
    is_terminal_app,
    match_app,
    run_shell,
)
from nexus.safety import redact_secrets

log = logging.getLogger("nexus.windows")

# Windows'da ishlaydigan asosiy (schemas.py) toollar
SUPPORTED_TOOLS = frozenset(
    {
        "launch_app",
        "list_applications",
        "quit_app",
        "set_volume",
        "mute_volume",
        "volume_step",
        "control_media",
        "get_system_info",
        "open_folder",
        "open_path",
        "send_notification",
        "lock_screen",
        "sleep_display",
        "toggle_dark_mode",
        "get_clipboard",
        "set_clipboard",
        "take_screenshot",
        "list_running_apps",
        "hide_all_windows",
        "empty_trash",
        "say_text",
        "start_dictation",
        "stop_dictation",
        "start_conversation",
        "stop_conversation",
        "browser_open_url",
        "web_search",
        "browser_switch_tab",
        "browser_close_tab",
        "browser_reload",
        "browser_current_page",
        "browser_list_tabs",
        "browser_scroll",
        "browser_click_button",
        "browser_read_page",
        "browser_type_and_search",
        "search_get_results",
        "search_open_result",
        "search_navigate_page",
        "youtube_control",
        "type_text",
        "press_hotkey",
        "run_terminal_command",
    }
)
# Windows'da yuklanadigan kengaytma modullari, tartib bilan (ax_actions/screen_reader o'rnini
# windows_screen egallaydi — tool nomlari bir xil)
WINDOWS_EXTENSION_MODULES: tuple[str, ...] = (
    "nexus.file_actions",
    "nexus.web_answer",
    "nexus.windows_screen",
    "nexus.video_translate",
)
SUPPORTED_EXTENSIONS = frozenset(WINDOWS_EXTENSION_MODULES)

# Virtual klavish kodlari (winuser.h)
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002
# Bitta ovoz klavishi Windows'da 2% o'zgartiradi
VOLUME_KEY_STEP = 2

MEDIA_KEYS = {
    "play_pause": (VK_MEDIA_PLAY_PAUSE, "ijro/pauza almashtirildi"),
    "play": (VK_MEDIA_PLAY_PAUSE, "ijro/pauza almashtirildi"),
    "pause": (VK_MEDIA_PLAY_PAUSE, "ijro/pauza almashtirildi"),
    "next": (VK_MEDIA_NEXT_TRACK, "keyingi trek"),
    "previous": (VK_MEDIA_PREV_TRACK, "oldingi trek"),
    "stop": (VK_MEDIA_STOP, "to'xtatildi"),
}

PROTECTED_PROCESSES = frozenset(
    {"explorer", "nexus", "nexus ovoz os", "csrss", "winlogon", "lsass", "services", "svchost", "dwm", "system"}
)


def _start_menu_dirs() -> list[Path]:
    dirs = []
    for env in ("PROGRAMDATA", "APPDATA"):
        base = os.environ.get(env)
        if base:
            dirs.append(Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    return dirs


_app_cache: tuple[float, dict[str, Path]] = (0.0, {})


def start_menu_apps(refresh: bool = False) -> dict[str, Path]:
    """Start menyusidagi yorliqlar: {ko'rinadigan nom: .lnk/.url yo'li} (60s kesh)."""
    global _app_cache
    now = time.monotonic()
    stamp, cached = _app_cache
    if not refresh and cached and now - stamp < APP_CACHE_TTL:
        return dict(cached)
    apps: dict[str, Path] = {}
    for folder in _start_menu_dirs():
        try:
            for p in folder.rglob("*"):
                if p.suffix.lower() in (".lnk", ".url", ".appref-ms"):
                    apps.setdefault(p.stem, p)
        except OSError:
            continue
    _app_cache = (now, apps)
    return dict(apps)


def _press_key(vk: int, times: int = 1) -> None:
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    for _ in range(times):
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def _ps_quote(s: str) -> str:
    """PowerShell bitta qo'shtirnoqli literal."""
    return "'" + str(s).replace("'", "''") + "'"


async def run_powershell(script: str, timeout: float = 15.0, stdin: bytes | None = None) -> Result:
    """PowerShell skriptini konsol oynasiz bajaradi; chiqish UTF-8."""
    prelude = "[Console]::OutputEncoding=[Text.Encoding]::UTF8;[Console]::InputEncoding=[Text.Encoding]::UTF8;"
    return await run_shell(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", prelude + script],
        timeout=timeout,
        stdin=stdin,
    )


class WindowsCommandGuard(CommandGuard):
    """`run_terminal_command` qo'riqchisi — Windows (cmd) buyruqlari uchun.

    Asosiy qoidalar `CommandGuard` dan: shell operatorlari rad etiladi, allowlist — tasdiqsiz,
    qolgani — tasdiq bilan, taqiqlangan token/yo'l — hech qachon. Windows'ga xos qo'shimchalar:
    buyruq nomi katta-kichik harfga va `.exe` ga bog'liq emas, `%VAR%` va `^` (cmd escape) taqiqlangan,
    `\\` li yo'llar buzilmaydi (`shlex` posix=False).
    """

    ALLOWED_FIRST = frozenset(
        {
            "dir", "echo", "type", "where", "whoami", "hostname", "ipconfig", "ping", "tasklist",
            "systeminfo", "ver", "vol", "tree", "findstr", "find", "git", "curl", "mkdir", "md",
            "copy", "move", "getmac", "nslookup", "date", "time", "fc",
        }
    )
    FORBIDDEN_TOKENS = CommandGuard.FORBIDDEN_TOKENS | frozenset(
        {
            "del", "erase", "rd", "format", "diskpart", "reg", "regedit", "bcdedit", "taskkill", "sc",
            "net", "net1", "netsh", "schtasks", "at", "powershell", "pwsh", "cmd", "wmic", "cipher",
            "vssadmin", "takeown", "icacls", "cacls", "attrib", "runas", "mshta", "rundll32", "regsvr32",
            "certutil", "bitsadmin", "wscript", "cscript", "start", "msiexec", "setx", "wevtutil", "fsutil",
            "sfc", "dism", "manage-bde", "robocopy", "xcopy", "forfiles", "logoff", "py", "pythonw",
            "invoke-expression", "iex", "remove-item", "set-executionpolicy", "call", "for", "goto", "set",
        }
    )
    FORBIDDEN_SUBSTRINGS = (*CommandGuard.FORBIDDEN_SUBSTRINGS, "%", "^", "\r")
    FORBIDDEN_PATH_PARTS = (
        ".ssh", ".gnupg", ".aws", ".env",
        "c:\\windows", "c:/windows", "system32", "syswow64",
        "program files", "programdata", "start menu\\programs\\startup", "start menu/programs/startup",
        "\\\\", "//",  # tarmoq (UNC) yo'llari
    )
    ARG_TOKEN_CHECKED = frozenset({"git", "curl", "where", "findstr", "find", "copy", "move", "dir", "type"})
    # cmd ichki buyruqlari — alohida .exe yo'q
    CMD_BUILTINS = frozenset({"dir", "echo", "type", "ver", "vol", "mkdir", "md", "copy", "move", "date", "time"})

    @staticmethod
    def split(command: str) -> list[str]:
        argv = [t[1:-1] if len(t) >= 2 and t[0] == t[-1] == '"' else t for t in shlex.split(command, posix=False)]
        if argv:
            first = argv[0].lower()
            argv[0] = first.removesuffix(".exe")
        return argv

    @staticmethod
    def argv(command: str) -> list[str]:
        return [os.path.expanduser(t) if t.startswith("~") else t for t in WindowsCommandGuard.split(command)]

    def _check_specific(self, first: str, rest: list[str]) -> Verdict | None:
        flags = [t.lower() for t in rest]
        if first == "ping":
            if "-t" in flags or "/t" in flags:
                return "deny", "ping -t (cheksiz) taqiqlangan"
            for opt in ("-n", "/n"):
                if opt in flags:
                    try:
                        n = int(rest[flags.index(opt) + 1])
                    except (IndexError, ValueError):
                        return "deny", "ping -n uchun son kerak"
                    if n < 1 or n > self.PING_MAX_COUNT:
                        return "deny", f"ping -n 1..{self.PING_MAX_COUNT} oralig'ida bo'lsin"
            return None
        if first in {"date", "time"}:
            return None if "/t" in flags else ("deny", f"{first} faqat /t bilan (aks holda kiritish kutadi)")
        if first in {"copy", "move"}:
            paths = [t for t in rest if not t.startswith("/")]
            if len(paths) < 2:
                return "deny", f"{first} uchun manba va manzil kerak"
            if "/y" in flags:
                return "confirm", f"{first} /y — mavjud faylni so'ramasdan almashtiradi"
            return None
        if first in {"git", "curl"}:
            return super()._check_specific(first, rest)
        return None


class WindowsController(MacOSController):
    """Windows bilan ishlash: ovoz, media, ilovalar, Explorer, tizim."""

    def __init__(self) -> None:
        self.guard = WindowsCommandGuard()

    # -- ovoz --------------------------------------------------------------
    async def set_volume(self, level: float) -> Result:
        try:
            lvl = int(_clamp(float(level), 0, 100))
        except (TypeError, ValueError):
            return False, "Ovoz darajasi 0..100 oralig'ida son bo'lishi kerak"
        # Mutlaq daraja API'siz: avval 0 gacha tushiramiz, keyin kerakli qadamlar
        await asyncio.to_thread(_press_key, VK_VOLUME_DOWN, 100 // VOLUME_KEY_STEP)
        await asyncio.to_thread(_press_key, VK_VOLUME_UP, round(lvl / VOLUME_KEY_STEP))
        return True, f"Ovoz {lvl}% ga o'rnatildi"

    async def mute_volume(self, mute: bool = True) -> Result:
        # Windows'da faqat almashtirish klavishi bor
        await asyncio.to_thread(_press_key, VK_VOLUME_MUTE)
        return True, "Ovoz o'chirildi/yoqildi"

    async def volume_step(self, delta: float) -> Result:
        try:
            step = int(float(delta))
        except (TypeError, ValueError):
            return False, "Ovoz qiymati noto'g'ri"
        if step == 0:
            return True, "Ovoz o'zgarmadi"
        presses = max(1, round(abs(step) / VOLUME_KEY_STEP))
        await asyncio.to_thread(_press_key, VK_VOLUME_UP if step > 0 else VK_VOLUME_DOWN, presses)
        return True, f"Ovoz {'oshirildi' if step > 0 else 'pasaytirildi'} ({abs(step)}%)"

    # -- media -------------------------------------------------------------
    async def media_control(self, action: str) -> Result:
        key = MEDIA_KEYS.get((action or "").lower().replace("-", "_"))
        if key is None:
            return False, f"Noma'lum media amali: {action} (play_pause|next|previous|stop)"
        vk, label = key
        await asyncio.to_thread(_press_key, vk)
        return True, f"Media: {label}"

    async def now_playing(self) -> Result:
        return False, "Windows'da hozir nima ijro etilayotganini aniqlash hali yo'q"

    async def set_brightness_keys(self, increase: bool = True, steps: int = 1) -> Result:
        return False, "Windows'da yorug'likni boshqarish hali yo'q"

    # -- ilovalar ----------------------------------------------------------
    async def launch_app(self, name: str) -> Result:
        name = (name or "").strip()
        if not name:
            return False, "Ilova nomi bo'sh"
        apps = await asyncio.to_thread(start_menu_apps)
        candidates = match_app(name, list(apps))
        if candidates:
            target = candidates[0]
            try:
                await asyncio.to_thread(os.startfile, str(apps[target]))  # type: ignore[attr-defined]
            except OSError as e:
                return False, f"'{target}' ochilmadi: {e}"
            others = [c for c in candidates[1:4] if c != target]
            suffix = f" (boshqa mosliklar: {', '.join(others)})" if others else ""
            return True, f"{target} ochildi{suffix}"
        # Yorliq yo'q — PATH/App Paths dagi dastur nomi bo'lishi mumkin (notepad, calc, ...)
        ok, out = await run_shell(["cmd", "/c", "start", "", name])
        if ok:
            return True, f"{name} ochildi"
        return False, f"'{name}' ilovasi topilmadi: {out}. list_applications bilan mavjud ilovalarni ko'ring."

    async def list_applications(self, filter_text: str | None = None) -> Result:
        apps = sorted(await asyncio.to_thread(start_menu_apps), key=str.lower)
        needle = (filter_text or "").strip().lower()
        if needle:
            apps = [a for a in apps if needle in a.lower()]
        if not apps:
            return True, "Mos ilova topilmadi" if needle else "O'rnatilgan ilovalar topilmadi"
        shown = apps[:200]
        more = f" (+{len(apps) - len(shown)} ta)" if len(apps) > len(shown) else ""
        return True, f"{len(apps)} ta ilova: {', '.join(shown)}{more}"

    async def quit_app(self, name: str) -> Result:
        name = (name or "").strip()
        if not name:
            return False, "Ilova nomi bo'sh"
        if name.lower().removesuffix(".exe") in PROTECTED_PROCESSES:
            return False, f"{name} ni yopish mumkin emas"
        return await asyncio.to_thread(self._quit_sync, name)

    @staticmethod
    def _quit_sync(name: str) -> Result:
        import psutil

        procs: dict[str, list[Any]] = {}
        for p in psutil.process_iter(["name"]):
            pname = (p.info.get("name") or "").removesuffix(".exe").removesuffix(".EXE")
            if pname:
                procs.setdefault(pname, []).append(p)
        matches = [m for m in match_app(name, list(procs)) if m.lower() not in PROTECTED_PROCESSES]
        if not matches:
            return False, f"'{name}' nomli ishlayotgan dastur topilmadi"
        target = matches[0]
        victims = procs[target]
        for p in victims:
            try:
                p.terminate()
            except psutil.Error:
                continue
        _, alive = psutil.wait_procs(victims, timeout=3)
        if alive:
            return False, f"{target} yopilmadi (ruxsat yo'q yoki javob bermayapti)"
        return True, f"{target} yopildi"

    async def hide_all_windows(self) -> Result:
        ok, out = await run_powershell("(New-Object -ComObject Shell.Application).MinimizeAll()")
        return (True, "Barcha oynalar yig'ildi") if ok else (False, f"Oynalarni yig'ib bo'lmadi: {out}")

    async def list_running_apps(self) -> Result:
        ok, out = await run_powershell(
            "Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object -ExpandProperty ProcessName "
            "| Sort-Object -Unique"
        )
        if not ok:
            return False, f"Ilovalar ro'yxatini olib bo'lmadi: {out}"
        names = [ln.strip() for ln in out.splitlines() if ln.strip()]
        return True, f"Ishlayotgan ilovalar: {', '.join(names)}" if names else "Ochiq oynali ilova yo'q"

    async def frontmost_app(self) -> Result:
        return await asyncio.to_thread(self._frontmost_sync)

    @staticmethod
    def _frontmost_sync() -> Result:
        try:
            import psutil

            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            hwnd = user32.GetForegroundWindow()
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return True, psutil.Process(pid.value).name().removesuffix(".exe")
        except Exception as e:  # noqa: BLE001
            return False, f"Faol ilovani aniqlab bo'lmadi: {e}"

    async def is_terminal_frontmost(self) -> bool:
        ok, name = await self.frontmost_app()
        low = name.lower()
        return ok and (is_terminal_app(name) or low in {"cmd", "powershell", "pwsh", "windowsterminal", "wt"})

    # -- Explorer ----------------------------------------------------------
    async def open_folder(self, path: str) -> Result:
        p = Path(os.path.expanduser((path or "").strip() or "~"))
        if not p.exists():
            return False, f"Papka topilmadi: {p}"
        if not p.is_dir():
            return False, f"Bu papka emas: {p}"
        try:
            await asyncio.to_thread(os.startfile, str(p))  # type: ignore[attr-defined]
        except OSError as e:
            return False, f"Papkani ochib bo'lmadi: {e}"
        return True, f"Papka ochildi: {p}"

    async def open_path(self, path: str) -> Result:
        raw = (path or "").strip()
        if not raw:
            return False, "Yo'l bo'sh"
        if "://" in raw:
            await asyncio.to_thread(webbrowser.open, raw)
            return True, f"Ochildi: {raw}"
        p = Path(os.path.expanduser(raw))
        if not p.exists():
            return False, f"Fayl yoki papka topilmadi: {p}"
        try:
            await asyncio.to_thread(os.startfile, str(p))  # type: ignore[attr-defined]
        except OSError as e:
            return False, f"Ochib bo'lmadi: {e}"
        return True, f"Ochildi: {p}"

    async def empty_trash(self) -> Result:
        ok, out = await run_powershell("Clear-RecycleBin -Force -ErrorAction Stop", timeout=60)
        return (True, "Savat tozalandi") if ok else (False, f"Savatni tozalab bo'lmadi: {out}")

    # -- tizim -------------------------------------------------------------
    async def lock_screen(self) -> Result:
        ok = await asyncio.to_thread(lambda: bool(ctypes.windll.user32.LockWorkStation()))  # type: ignore[attr-defined]
        return (True, "Ekran qulflandi") if ok else (False, "Ekranni qulflab bo'lmadi")

    async def sleep_display(self) -> Result:
        def _off() -> None:
            # HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2 = o'chirish
            ctypes.windll.user32.PostMessageW(0xFFFF, 0x0112, 0xF170, 2)  # type: ignore[attr-defined]

        await asyncio.to_thread(_off)
        return True, "Ekran uxlatildi"

    async def send_notification(self, title: str, message: str) -> Result:
        script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$n=New-Object System.Windows.Forms.NotifyIcon;"
            "$n.Icon=[System.Drawing.SystemIcons]::Information;$n.Visible=$true;"
            f"$n.ShowBalloonTip(5000,{_ps_quote(title)},{_ps_quote(message)},'Info');"
            "Start-Sleep -Seconds 6;$n.Dispose()"
        )
        ok, out = await run_powershell(script, timeout=15)
        return (True, "Bildirishnoma ko'rsatildi") if ok else (False, f"Bildirishnoma ko'rsatilmadi: {out}")

    async def say_text(self, text: str, voice: str | None = None) -> Result:
        text = (text or "").strip()
        if not text:
            return False, "Matn bo'sh"
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$s.Speak([Console]::In.ReadToEnd())"
        )
        ok, out = await run_powershell(script, timeout=120, stdin=text.encode("utf-8"))
        return (True, "Matn o'qib berildi") if ok else (False, f"O'qib bo'lmadi: {out}")

    async def toggle_dark_mode(self) -> Result:
        return await asyncio.to_thread(self._toggle_dark_sync)

    @staticmethod
    def _toggle_dark_sync() -> Result:
        import winreg  # type: ignore[import-not-found]

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                try:
                    light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                except FileNotFoundError:
                    light = 1
                new = 0 if light else 1
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, new)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, new)
        except OSError as e:
            return False, f"Rejimni almashtirib bo'lmadi: {e}"
        return True, "Yorug' rejim yoqildi" if new else "Qorong'u rejim yoqildi"

    async def set_do_not_disturb(self, on: bool = True) -> Result:
        return False, "Windows'da bezovta qilmaslik rejimini boshqarish hali yo'q"

    # -- bufer -------------------------------------------------------------
    async def _clipboard_read(self) -> Result:
        return await run_powershell("Get-Clipboard -Raw")

    async def _clipboard_write(self, text: str) -> Result:
        return await run_powershell(
            "Set-Clipboard -Value ([Console]::In.ReadToEnd())", stdin=(text or "").encode("utf-8")
        )

    async def get_clipboard(self) -> Result:
        ok, out = await self._clipboard_read()
        if not ok:
            return False, f"Buferni o'qib bo'lmadi: {out}"
        return True, _truncate(redact_secrets(out)) if out else "Bufer bo'sh"

    async def type_text(self, text: str, press_enter: bool = False) -> Result:
        """Faol oynaga matn teradi (SendInput Unicode — bufer o'zgarmaydi)."""
        from nexus import windows_input

        if not text:
            return False, "Matn bo'sh"
        text = text[: windows_input.MAX_TYPE_CHARS]
        try:
            await asyncio.to_thread(windows_input.type_unicode, text)
            if press_enter:
                await asyncio.sleep(0.1)
                await asyncio.to_thread(windows_input.press_enter)
        except OSError as e:
            return False, f"Matnni terib bo'lmadi: {e}"
        msg = f"Matn terildi ({len(text)} belgi)"
        return True, msg + (" va Enter bosildi" if press_enter else "")

    async def press_hotkey(self, keys: str) -> Result:
        from nexus import windows_input

        try:
            windows_input.parse_hotkey(keys)
            await asyncio.to_thread(windows_input.press_combo, keys)
        except windows_input.HotkeyError as e:
            return False, str(e)
        except OSError as e:
            return False, f"Klavishlarni bosib bo'lmadi: {e}"
        return True, f"Bosildi: {keys}"

    async def take_screenshot(self, target_path: str | None = None) -> Result:
        if target_path:
            path = Path(os.path.expanduser(target_path))
        else:
            stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
            path = Path(os.path.expanduser(settings.screenshot_dir)) / f"nexus_{stamp}.png"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"Papka yaratib bo'lmadi: {e}"
        script = (
            "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
            "$b=[System.Windows.Forms.SystemInformation]::VirtualScreen;"
            "$bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;"
            "$g=[System.Drawing.Graphics]::FromImage($bmp);"
            "$g.CopyFromScreen($b.Left,$b.Top,0,0,$bmp.Size);"
            f"$bmp.Save({_ps_quote(str(path))},[System.Drawing.Imaging.ImageFormat]::Png);"
            "$g.Dispose();$bmp.Dispose()"
        )
        ok, out = await run_powershell(script, timeout=20)
        if not ok or not path.exists():
            return False, f"Skrinshot olinmadi: {out}"
        return True, f"Skrinshot saqlandi: {path}"

    async def get_system_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "hostname": platform.node(),
            "windows_version": f"{platform.release()} ({platform.version()})",
            "cpu_percent": None,
            "ram_percent": None,
            "ram_used_gb": None,
            "ram_total_gb": None,
            "battery_percent": None,
            "battery_charging": None,
            "uptime": None,
            "uptime_seconds": None,
            "disk_free_gb": None,
            "disk_total_gb": None,
        }
        try:
            import psutil

            info["cpu_percent"] = round(await asyncio.to_thread(psutil.cpu_percent, 0.3), 1)
            vm = psutil.virtual_memory()
            info["ram_percent"] = round(vm.percent, 1)
            info["ram_used_gb"] = round((vm.total - vm.available) / 1e9, 2)
            info["ram_total_gb"] = round(vm.total / 1e9, 2)
            batt = psutil.sensors_battery()
            if batt is not None:
                info["battery_percent"] = int(batt.percent)
                info["battery_charging"] = bool(batt.power_plugged)
            secs = int(time.time() - psutil.boot_time())
            info["uptime_seconds"] = secs
            info["uptime"] = _fmt_uptime(secs)
        except Exception as e:  # noqa: BLE001
            log.warning("psutil ma'lumotlari olinmadi: %s", e)
        try:
            du = shutil.disk_usage(os.environ.get("SYSTEMDRIVE", "C:") + "\\")
            info["disk_free_gb"] = round(du.free / 1e9, 1)
            info["disk_total_gb"] = round(du.total / 1e9, 1)
        except OSError:
            pass
        summary = _summarize_info(info)
        info["summary"] = f"{summary}; Windows {platform.release()}"
        return info

    # -- terminal ----------------------------------------------------------
    async def run_terminal_command(self, command: str, confirmed: bool = False) -> Result:
        """Buyruqni qo'riqchi orqali `cmd` da bajaradi (UTF-8 kod sahifasi, shell operatorlarisiz)."""
        if not settings.allow_terminal:
            return False, "Terminal buyruqlari sozlamalarda o'chirilgan (ALLOW_TERMINAL=false)"
        verdict, reason = self.guard.check(command)
        if verdict == "deny":
            return False, f"Buyruq rad etildi: {reason}"
        if verdict == "confirm" and not confirmed:
            return False, f"Tasdiq kerak: {reason}"
        argv = WindowsCommandGuard.argv(command)
        # chcp 65001 — chiqish UTF-8 bo'lsin (aks holda OEM kod sahifasi: kirill/o'zbekcha buziladi)
        line = "chcp 65001>nul & " + subprocess.list2cmdline(argv)
        ok, out = await run_shell(["cmd", "/d", "/s", "/c", line], timeout=15)
        out = _truncate(redact_secrets(out), MAX_OUTPUT_CHARS)
        if ok:
            return True, out or "(chiqish bo'sh)"
        return False, out or "Buyruq xato bilan tugadi"

    # -- ruxsatlar ---------------------------------------------------------
    async def check_permissions(self) -> dict[str, Any]:
        # Windows'da macOS'dagidek TCC ruxsatlari yo'q; mikrofon — Sozlamalar → Maxfiylik → Mikrofon
        return {"hints": [], "message": "Windows: alohida ruxsat talab qilinmaydi."}


WINDOWS_BROWSER_PARAM: dict[str, Any] = {
    "type": "STRING",
    "enum": ["chrome", "edge", "firefox"],
    "description": "Which browser to control. If unspecified by the user, leave empty (the open browser is used).",
}


def adapt_declaration(decl: dict[str, Any]) -> dict[str, Any]:
    """Tool deklaratsiyasini Windows'ga moslaydi: brauzer enum'i, macOS so'zlari."""
    props = (decl.get("parameters") or {}).get("properties") or {}
    desc = str(decl.get("description", ""))
    if decl.get("name") == "translate_video":
        # Windows'da video Nexus'ning o'z oynasida ochiladi — brauzer tanlanmaydi
        props = {k: v for k, v in props.items() if k != "browser"}
        desc = desc.replace("Open a YouTube video in the browser", "Open a YouTube video in a Nexus video window")
        return {**decl, "description": desc, "parameters": {**decl["parameters"], "properties": props}}
    for old, new in (("Safari or Chrome", "the browser"), ("macOS ", ""), ("Finder", "File Explorer"), ("cmd+", "ctrl+")):
        desc = desc.replace(old, new)
    if "browser" not in props and desc == decl.get("description"):
        return decl
    out = {**decl, "description": desc}
    if "browser" in props:
        out["parameters"] = {**decl["parameters"], "properties": {**props, "browser": WINDOWS_BROWSER_PARAM}}
    return out


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_TOOLS",
    "WindowsCommandGuard",
    "WindowsController",
    "adapt_declaration",
    "run_powershell",
    "start_menu_apps",
]
