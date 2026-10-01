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
import shutil
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

from nexus.browser_actions import normalize_url
from nexus.config import settings
from nexus.macos_actions import (
    APP_CACHE_TTL,
    MacOSController,
    Result,
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

# Windows'da ishlaydigan asosiy (schemas.py) toollar. Qolganlari 2-bosqichda.
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
    }
)
# Windows'da ishlaydigan kengaytma modullari (qolganlari pyobjc/AppleScript'ga bog'liq)
SUPPORTED_EXTENSIONS = frozenset({"nexus.file_actions", "nexus.web_answer"})

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


class WindowsController(MacOSController):
    """Windows bilan ishlash: ovoz, media, ilovalar, Explorer, tizim."""

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
        return False, "Windows'da matn terish hali yo'q (2-bosqich)"

    async def press_hotkey(self, keys: str) -> Result:
        return False, "Windows'da klavish bosish hali yo'q (2-bosqich)"

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
        return False, "Windows'da terminal buyruqlari hali yo'q (2-bosqich)"

    # -- ruxsatlar ---------------------------------------------------------
    async def check_permissions(self) -> dict[str, Any]:
        # Windows'da macOS'dagidek TCC ruxsatlari yo'q; mikrofon — Sozlamalar → Maxfiylik → Mikrofon
        return {"hints": [], "message": "Windows: alohida ruxsat talab qilinmaydi."}


class WindowsBrowserController:
    """Windows'da brauzer: hozircha faqat URL'ni standart (yoki tanlangan) brauzerda ochish."""

    async def open_url(self, browser: str, url: str) -> Result:
        target = normalize_url(url)
        ok = await asyncio.to_thread(webbrowser.open, target, 2)
        if not ok:
            return False, f"Sahifani ochib bo'lmadi: {target}"
        return True, f"Brauzerda ochildi: {target}"


__all__ = [
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_TOOLS",
    "WindowsBrowserController",
    "WindowsController",
    "run_powershell",
    "start_menu_apps",
]
