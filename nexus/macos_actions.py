"""macOS tizim amallari (AppleScript + xavfsiz shell).

Barcha subprocess chaqiruvlari `asyncio.create_subprocess_exec` orqali —
hech qachon `shell=True`, hech qachon bloklovchi `subprocess.run` yo'q.
Har bir metod `(ok: bool, out: str)` juftligini qaytaradi; `out` — foydalanuvchiga
o'qib berish uchun yaroqli o'zbekcha matn yoki qisqa natija.
"""

from __future__ import annotations

import asyncio
import ctypes
import json
import logging
import os
import platform
import re
import shlex
import shutil
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from nexus.config import settings
from nexus.safety import path_is_sensitive, redact_secrets, shell_is_dangerous

log = logging.getLogger("nexus.macos")

MAX_OUTPUT_CHARS = 4000
DEFAULT_TIMEOUT = 15.0

Result = tuple[bool, str]


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------
def _as_str(s: Any) -> str:
    """Python qiymatini AppleScript satr literaliga (qo'shtirnoq ichida) xavfsiz aylantiradi.

    `\\` → `\\\\`, `"` → `\\"`, yangi qator → `\\n`, tab → `\\t`. Natija qo'shtirnoq bilan o'ralgan.
    """
    text = str(s)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", "\\n").replace("\t", "\\t")
    return f'"{text}"'


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… [{len(text) - limit} belgi qisqartirildi]"


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


if sys.platform == "win32":
    # Oynasiz .exe'dan PowerShell/cmd chaqirilganda qora konsol oynasi chiqmasin
    _SPAWN_KWARGS: dict[str, Any] = {"creationflags": 0x08000000}  # CREATE_NO_WINDOW
else:
    # o'z process group'i — timeout'da butun daraxt o'ldiriladi
    _SPAWN_KWARGS = {"start_new_session": True}


async def run_shell(argv: list[str], timeout: float = DEFAULT_TIMEOUT, stdin: bytes | None = None) -> Result:
    """Dasturni shell'siz ishga tushiradi. `(ok, stdout yoki stderr)` qaytaradi."""
    if not argv:
        return False, "Bo'sh buyruq"
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **_SPAWN_KWARGS,
        )
    except FileNotFoundError:
        return False, f"Dastur topilmadi: {argv[0]}"
    except PermissionError:
        return False, f"Ruxsat yo'q: {argv[0]}"
    except OSError as e:
        return False, f"Ishga tushirib bo'lmadi: {e}"

    try:
        out_b, err_b = await asyncio.wait_for(proc.communicate(stdin), timeout=timeout)
    except TimeoutError:
        _kill_process_group(proc)
        with _suppress():
            await proc.wait()
        return False, f"Vaqt tugadi ({timeout:.0f}s): {' '.join(argv[:3])}"
    except asyncio.CancelledError:
        _kill_process_group(proc)
        raise

    out = out_b.decode("utf-8", "replace").strip()
    err = err_b.decode("utf-8", "replace").strip()
    if proc.returncode == 0:
        return True, out
    return False, err or out or f"Xato (kod {proc.returncode})"


async def run_applescript(script: str, timeout: float = DEFAULT_TIMEOUT) -> Result:
    """AppleScript'ni `osascript` orqali bajaradi (stdin orqali, argument uzunligi cheklovisiz)."""
    ok, out = await run_shell(["osascript", "-"], timeout=timeout, stdin=script.encode("utf-8"))
    if not ok:
        # osascript xatosi: "123:45: execution error: ... (-1743)" ko'rinishida bo'ladi
        out = re.sub(r"^\d+:\d+:\s*", "", out)
    return ok, out


class _suppress:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *exc: object) -> bool:
        return True


def _kill_process_group(proc: asyncio.subprocess.Process) -> None:
    """Jarayonni va u tug'dirgan barcha bolalarni (process group) o'ldiradi."""
    if proc.returncode is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)  # Windows'da killpg yo'q → AttributeError → proc.kill()
    except (ProcessLookupError, PermissionError, OSError, AttributeError):
        with _suppress():
            proc.kill()


# ---------------------------------------------------------------------------
# Terminal buyruqlari uchun qat'iy qo'riqchi
# ---------------------------------------------------------------------------
Verdict = tuple[str, str]  # ("allow" | "confirm" | "deny", sabab)


class CommandGuard:
    """`run_terminal_command` uchun uch pog'onali qo'riqchi.

    `check()` → ("allow" | "confirm" | "deny", sabab):
      - deny    — DANGEROUS_SHELL naqshi, taqiqlangan token/yo'l, shell operatorlari,
                  yoki osilib qoladigan chaqiruv (ping -c siz, top -l siz). HECH QACHON bajarilmaydi.
      - allow   — allowlist'dagi buyruq, o'ziga xos cheklovlardan o'tgan va sezgir yo'lga tegmaydi.
      - confirm — qolgan hamma narsa (allowlist'dan tashqari, lekin xavfli emas; yozuvchi
                  bayroqlar; sezgir yo'l) — foydalanuvchi tasdig'i bilan bajariladi.

    Buyruq `shlex.split` bilan bo'linadi va shell'siz bajariladi, shuning uchun
    `|`, `>`, `;` kabi belgilar baribir ishlamaydi — lekin ular baribir rad etiladi.
    """

    ALLOWED_FIRST = frozenset(
        {
            "ls",
            "pwd",
            "cat",
            "head",
            "tail",
            "wc",
            "echo",
            "date",
            "whoami",
            "uname",
            "uptime",
            "df",
            "du",
            "ps",
            "top",
            "grep",
            "find",
            "which",
            "open",
            "ping",
            "curl",
            "brew",
            "git",
            "mkdir",
            "touch",
            "cp",
            "mv",
            "say",
            "stat",
            "file",
            "hostname",
            "sw_vers",
            "diff",
            "shasum",
            "md5",
            "cal",
        }
    )

    FORBIDDEN_TOKENS = frozenset(
        {
            "rm",
            "rmdir",
            "sudo",
            "su",
            "doas",
            "killall",
            "kill",
            "pkill",
            "shutdown",
            "reboot",
            "halt",
            "poweroff",
            "diskutil",
            "dd",
            "mkfs",
            "chown",
            "chmod",
            "launchctl",
            "defaults",
            "nvram",
            "csrutil",
            "eval",
            "exec",
            "osascript",
            "sh",
            "bash",
            "zsh",
            "fish",
            "python",
            "python3",
            "perl",
            "ruby",
            "node",
            "xargs",
            "env",
            "nohup",
            "tee",
            "srm",
            "shred",
            "systemsetup",
            "scutil",
            "networksetup",
            "spctl",
            "tccutil",
            "security",
            "passwd",
            "crontab",
        }
    )

    FORBIDDEN_SUBSTRINGS = (
        ">",
        "|",
        ";",
        "&&",
        "||",
        "`",
        "$(",
        "${",
        "&",
        "\n",
    )

    FORBIDDEN_PATH_PARTS = (
        ".ssh",
        "/etc",
        "/private/etc",
        "/system",
        "/library/keychains",
        "keychains",
        "/var/db",
        "/usr/bin",
        "/usr/sbin",
        "/bin/",
        "/sbin",
        "/dev/",
        ".gnupg",
        ".aws",
        ".env",
    )

    BREW_ALLOWED = frozenset({"list", "info", "search", "outdated", "--version", "-v"})
    GIT_ALLOWED = frozenset({"status", "log", "diff", "branch", "show", "--version"})
    FIND_FORBIDDEN = frozenset({"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf"})
    CURL_WRITE_PREFIXES = (
        "-X",
        "--request",
        "-d",
        "--data",
        "-F",
        "--form",
        "-T",
        "--upload-file",
        "-u",
        "--user",
        "-K",
        "--config",
        "-c",
        "--cookie-jar",
    )
    CURL_DENY_PREFIXES = ("-o", "--output", "-O", "--remote-name", "--proto")
    PING_MAX_COUNT = 5
    # Argumentlari orasida taqiqlangan tokenlar tekshiriladigan buyruqlar
    # (`which rm` yoki `echo sudo` zararsiz, lekin `find -exec rm` emas)
    ARG_TOKEN_CHECKED = frozenset({"find", "git", "brew", "curl", "open", "top", "ps", "mv", "cp"})

    def check(self, command: str) -> Verdict:
        raw = (command or "").strip()
        if not raw:
            return "deny", "Bo'sh buyruq"
        if len(raw) > 500:
            return "deny", "Buyruq juda uzun (500 belgidan oshmasin)"

        for sub in self.FORBIDDEN_SUBSTRINGS:
            if sub in raw:
                return "deny", f"Taqiqlangan belgi: {sub.strip() or 'yangi qator'}"

        if shell_is_dangerous(raw):
            return "deny", "Xavfli buyruq naqshi (DANGEROUS_SHELL)"

        try:
            argv = self.split(raw)
        except ValueError as e:
            return "deny", f"Buyruqni o'qib bo'lmadi: {e}"
        if not argv:
            return "deny", "Bo'sh buyruq"

        first = os.path.basename(argv[0])
        if first in self.FORBIDDEN_TOKENS:
            return "deny", f"Taqiqlangan buyruq: {first}"
        if argv[0] != first:
            return "deny", "Buyruq nomi to'liq yo'l bilan berilmasin"

        sensitive_tok: str | None = None
        for tok in argv[1:]:
            base = os.path.basename(tok)
            if first in self.ARG_TOKEN_CHECKED and (
                tok in self.FORBIDDEN_TOKENS or base in self.FORBIDDEN_TOKENS
            ):
                return "deny", f"Taqiqlangan token: {tok}"
            expanded = os.path.expanduser(tok).lower()
            for part in self.FORBIDDEN_PATH_PARTS:
                if part in expanded or part in tok.lower():
                    return "deny", f"Taqiqlangan yo'l: {tok}"
            looks_like_path = "/" in tok or "\\" in tok or tok.startswith(("~", "."))
            if (
                sensitive_tok is None
                and not tok.startswith("-")
                and looks_like_path
                and path_is_sensitive(tok)
            ):
                sensitive_tok = tok

        if first not in self.ALLOWED_FIRST:
            return "confirm", f"Allowlist'dan tashqari buyruq: {first}"

        specific = self._check_specific(first, argv[1:])
        if specific is not None:
            verdict, reason = specific
            return verdict, reason
        if sensitive_tok is not None:
            return "confirm", f"Sezgir yo'l: {sensitive_tok}"
        return "allow", "ok"

    def _check_specific(self, first: str, rest: list[str]) -> Verdict | None:
        if first == "find":
            for tok in rest:
                if tok in self.FIND_FORBIDDEN:
                    return "deny", f"find uchun {tok} taqiqlangan"
        elif first == "top":
            if "-l" not in rest:
                return "deny", "top faqat `top -l 1` ko'rinishida ruxsat etilgan"
            try:
                n = int(rest[rest.index("-l") + 1])
            except (IndexError, ValueError):
                return "deny", "top -l uchun son kerak (masalan `top -l 1`)"
            if n < 1 or n > 3:
                return "deny", "top -l 1..3 oralig'ida bo'lsin"
        elif first == "ping":
            if "-c" not in rest:
                return "deny", "ping faqat `-c N` bilan (N ≤ 5) ruxsat etilgan"
            try:
                n = int(rest[rest.index("-c") + 1])
            except (IndexError, ValueError):
                return "deny", "ping -c uchun son kerak"
            if n < 1 or n > self.PING_MAX_COUNT:
                return "deny", f"ping -c 1..{self.PING_MAX_COUNT} oralig'ida bo'lsin"
            if "-f" in rest or "-i" in rest:
                return "deny", "ping -f / -i taqiqlangan"
        elif first == "curl":
            for tok in rest:
                if tok.startswith("--"):
                    if any(tok == p or tok.startswith(p + "=") for p in self.CURL_DENY_PREFIXES):
                        return "deny", f"curl uchun {tok} taqiqlangan"
                    if any(tok == p or tok.startswith(p + "=") for p in self.CURL_WRITE_PREFIXES):
                        return "confirm", f"curl {tok} — ma'lumot yuboradi (faqat GET tez yo'l)"
                elif tok.startswith("-") and len(tok) > 1:
                    # -sSLX kabi birlashgan bayroqlar: har bir harfni tekshiramiz
                    for ch in tok[1:]:
                        if "-" + ch in self.CURL_DENY_PREFIXES:
                            return "deny", f"curl uchun -{ch} taqiqlangan"
                        if "-" + ch in self.CURL_WRITE_PREFIXES:
                            return "confirm", f"curl -{ch} — ma'lumot yuboradi (faqat GET tez yo'l)"
                elif tok.lower().startswith(("file:", "ftp:", "sftp:", "smb:", "gopher:", "dict:")):
                    return "deny", "curl faqat http/https bilan ishlaydi"
        elif first == "brew":
            if not rest or rest[0] not in self.BREW_ALLOWED:
                return "confirm", "brew faqat list/info/search/outdated tez yo'lda; qolgani tasdiq bilan"
        elif first == "git":
            if not rest or rest[0] not in self.GIT_ALLOWED:
                return "confirm", "git faqat status/log/diff/branch/show tez yo'lda; qolgani tasdiq bilan"
            for tok in rest[1:]:
                if tok in {"-D", "-d", "--delete", "-m", "-M", "--move"}:
                    return "confirm", f"git branch {tok} — o'zgartiruvchi amal"
        elif first == "open":
            for tok in rest:
                if tok in {"-W", "--wait-apps"}:
                    return "deny", "open -W taqiqlangan (bloklaydi)"
        elif first in {"cp", "mv"}:
            if len(rest) < 2:
                return "deny", f"{first} uchun manba va manzil kerak"
            for tok in rest:
                if tok.startswith("-") and any(ch in tok for ch in "Rrf"):
                    return "confirm", f"{first} {tok} — rekursiv/majburiy nusxalash"
        elif first == "mkdir":
            for tok in rest:
                if tok.startswith("-") and tok not in {"-p", "-v", "-pv", "-vp"}:
                    return "confirm", f"mkdir uchun {tok} bayrog'i"
        return None

    @staticmethod
    def split(command: str) -> list[str]:
        """Buyruqni tokenlarga bo'lish (POSIX qoidalari). Windows qo'riqchisi qayta belgilaydi."""
        return shlex.split(command)

    @staticmethod
    def argv(command: str) -> list[str]:
        """Tekshiruvdan o'tgan buyruqni bajarish uchun argv (`~` kengaytirilgan holda)."""
        return [os.path.expanduser(t) if t.startswith("~") else t for t in shlex.split(command)]


# ---------------------------------------------------------------------------
# Asosiy boshqaruvchi
# ---------------------------------------------------------------------------
_HOTKEY_MODIFIERS = {
    "cmd": "command down",
    "command": "command down",
    "meta": "command down",
    "shift": "shift down",
    "alt": "option down",
    "option": "option down",
    "opt": "option down",
    "ctrl": "control down",
    "control": "control down",
}

_HOTKEY_KEYCODES = {
    "enter": 36,
    "return": 36,
    "tab": 48,
    "space": 49,
    "delete": 51,
    "backspace": 51,
    "forwarddelete": 117,
    "esc": 53,
    "escape": 53,
    "left": 123,
    "right": 124,
    "down": 125,
    "up": 126,
    "home": 115,
    "end": 119,
    "pageup": 116,
    "pagedown": 121,
    "f1": 122,
    "f2": 120,
    "f3": 99,
    "f4": 118,
    "f5": 96,
    "f6": 97,
    "f7": 98,
    "f8": 100,
    "f9": 101,
    "f10": 109,
    "f11": 103,
    "f12": 111,
}


# ---------------------------------------------------------------------------
# Ilovalarni topish (fuzzy)
# ---------------------------------------------------------------------------
APP_FOLDERS = (
    Path("/Applications"),
    Path("/Applications/Utilities"),
    Path("/System/Applications"),
    Path("/System/Applications/Utilities"),
    Path.home() / "Applications",
)
APP_CACHE_TTL = 60.0
_app_cache: tuple[float, list[str]] = (0.0, [])

# Terilgan matn Enter bosilishi bilan buyruq sifatida bajariladigan ilovalar.
TERMINAL_APPS = frozenset(
    {
        "terminal",
        "iterm",
        "iterm2",
        "warp",
        "alacritty",
        "kitty",
        "wezterm",
        "hyper",
        "tabby",
        "rio",
        "ghostty",
        "wave",
        "cool retro term",
    }
)
_APP_NOISE_WORDS = (
    "uninstall",
    "helper",
    "updater",
    "update",
    "installer",
    "setup",
    "crash",
    "diagnostic",
    "agent",
)


def installed_apps(refresh: bool = False) -> list[str]:
    """/Applications, /System/Applications, ~/Applications dagi .app nomlari (60s kesh)."""
    global _app_cache
    now = time.monotonic()
    stamp, cached = _app_cache
    if not refresh and cached and now - stamp < APP_CACHE_TTL:
        return list(cached)
    names: set[str] = set()
    for folder in APP_FOLDERS:
        try:
            if folder.is_dir():
                names.update(p.stem for p in folder.glob("*.app"))
        except OSError:
            continue
    result = sorted(names, key=str.lower)
    _app_cache = (now, result)
    return list(result)


def _starts_a_word(haystack: str, needle: str) -> bool:
    """`needle` nomning boshida yoki ichidagi so'z boshida keladi ("word" ≠ "Passwords")."""
    if not needle:
        return False
    for index in range(len(haystack) - len(needle) + 1):
        if haystack.startswith(needle, index) and (index == 0 or not haystack[index - 1].isalnum()):
            return True
    return False


def match_app(name: str, apps: list[str] | None = None) -> list[str]:
    """Aytilgan nomga mos o'rnatilgan ilovalar, eng yaqini birinchi.

    Tartib: aniq moslik → bo'shliqsiz moslik → so'z boshi mosligi → so'rovdagi
    alohida uzun so'z bo'yicha moslik. "Uninstall"/"Helper" kabi yordamchi
    bundle'lar oxiriga suriladi.
    """
    apps = installed_apps() if apps is None else list(apps)
    wanted = (name or "").strip().lower()
    if not wanted:
        return []
    squashed = wanted.replace(" ", "")

    def by_length(names: list[str]) -> list[str]:
        return sorted(set(names), key=lambda a: (len(a), a.lower()))

    exact = [a for a in apps if a.lower() == wanted]
    if exact:
        return exact
    tight = [a for a in apps if a.lower().replace(" ", "") == squashed]
    if tight:
        return by_length(tight)

    def hits(app: str, needle: str) -> bool:
        lower = app.lower()
        return _starts_a_word(lower, needle) or _starts_a_word(
            lower.replace(" ", ""), needle.replace(" ", "")
        )

    def rank(app: str) -> tuple[int, int, int, str]:
        noise = 1 if any(w in app.lower() for w in _APP_NOISE_WORDS) else 0
        starts = 0 if app.lower().startswith(wanted) else 1
        return noise, starts, len(app), app.lower()

    loose = [a for a in apps if hits(a, wanted)]
    if loose:
        return sorted(set(loose), key=rank)
    words = [w for w in wanted.split() if len(w) > 3]
    return sorted({a for a in apps if any(hits(a, w) for w in words)}, key=rank)


_match_app = match_app  # eski nom (moslik uchun)


def is_terminal_app(name: str | None) -> bool:
    low = (name or "").strip().lower()
    return bool(low) and any(term in low for term in TERMINAL_APPS)


class MacOSController:
    """macOS bilan ishlash: ovoz, media, ilovalar, Finder, tizim, terminal."""

    def __init__(self) -> None:
        self.guard = CommandGuard()

    # -- asos --------------------------------------------------------------
    async def run_applescript(self, script: str, timeout: float = DEFAULT_TIMEOUT) -> Result:
        return await run_applescript(script, timeout=timeout)

    async def run_shell(self, argv: list[str], timeout: float = DEFAULT_TIMEOUT) -> Result:
        return await run_shell(argv, timeout=timeout)

    # -- ovoz --------------------------------------------------------------
    async def set_volume(self, level: float) -> Result:
        try:
            lvl = int(_clamp(float(level), 0, 100))
        except (TypeError, ValueError):
            return False, "Ovoz darajasi 0..100 oralig'ida son bo'lishi kerak"
        ok, out = await self.run_applescript(f"set volume output volume {lvl}")
        return (True, f"Ovoz {lvl}% ga o'rnatildi") if ok else (False, f"Ovozni o'rnatib bo'lmadi: {out}")

    async def mute_volume(self, mute: bool = True) -> Result:
        flag = "true" if mute else "false"
        ok, out = await self.run_applescript(f"set volume output muted {flag}")
        if not ok:
            return False, f"Ovozni o'chirib bo'lmadi: {out}"
        return True, "Ovoz o'chirildi" if mute else "Ovoz yoqildi"

    async def get_volume(self) -> Result:
        script = (
            "set s to get volume settings\n"
            'return (output volume of s as text) & "|" & (output muted of s as text)'
        )
        ok, out = await self.run_applescript(script)
        if not ok:
            return False, f"Ovoz darajasini o'qib bo'lmadi: {out}"
        vol, _, muted = out.partition("|")
        suffix = " (o'chirilgan)" if muted.strip() == "true" else ""
        return True, f"Ovoz darajasi: {vol.strip()}%{suffix}"

    async def volume_step(self, delta: float) -> Result:
        ok, out = await self.run_applescript("output volume of (get volume settings)")
        if not ok:
            return False, f"Ovoz darajasini o'qib bo'lmadi: {out}"
        try:
            current = int(float(out.strip()))
            step = int(float(delta))
        except ValueError:
            return False, "Ovoz qiymati noto'g'ri"
        return await self.set_volume(current + step)

    # -- media -------------------------------------------------------------
    async def _media_app(self) -> str:
        ok, out = await self.run_applescript(
            'tell application "System Events" to return (name of processes) contains "Spotify"'
        )
        return "Spotify" if ok and out.strip() == "true" else "Music"

    async def media_control(self, action: str) -> Result:
        actions = {
            "play_pause": "playpause",
            "play": "play",
            "pause": "pause",
            "next": "next track",
            "previous": "previous track",
            "stop": "stop",
        }
        cmd = actions.get((action or "").lower().replace("-", "_"))
        if cmd is None:
            return False, f"Noma'lum media amali: {action} (play_pause|next|previous|stop)"
        app = await self._media_app()
        ok, out = await self.run_applescript(f'tell application "{app}" to {cmd}')
        if not ok:
            return False, f"{app}: {out}"
        labels = {
            "playpause": "ijro/pauza almashtirildi",
            "play": "ijro boshlandi",
            "pause": "pauza qilindi",
            "next track": "keyingi trek",
            "previous track": "oldingi trek",
            "stop": "to'xtatildi",
        }
        return True, f"{app}: {labels[cmd]}"

    async def now_playing(self) -> Result:
        app = await self._media_app()
        script = (
            f'tell application "{app}"\n'
            '  if player state is stopped then return "stopped"\n'
            "  set t to current track\n"
            '  return (name of t) & " — " & (artist of t) & " | " & (player state as text)\n'
            "end tell"
        )
        ok, out = await self.run_applescript(script)
        if not ok:
            return False, f"{app}: {out}"
        if out.strip() == "stopped":
            return True, f"{app}: hozir hech narsa ijro etilmayapti"
        return True, f"{app}: {out}"

    # -- yorug'lik ---------------------------------------------------------
    async def set_brightness_keys(self, increase: bool = True, steps: int = 1) -> Result:
        code = 144 if increase else 145
        n = int(_clamp(int(steps or 1), 1, 16))
        script = (
            'tell application "System Events"\n'
            f"  repeat {n} times\n"
            f"    key code {code}\n"
            "    delay 0.05\n"
            "  end repeat\n"
            "end tell"
        )
        ok, out = await self.run_applescript(script)
        if not ok:
            return False, f"Yorug'likni o'zgartirib bo'lmadi (Accessibility ruxsati kerak): {out}"
        return True, f"Yorug'lik {n} pog'ona {'oshirildi' if increase else 'kamaytirildi'}"

    # -- ilovalar ----------------------------------------------------------
    async def launch_app(self, name: str) -> Result:
        name = (name or "").strip()
        if not name:
            return False, "Ilova nomi bo'sh"
        candidates = await asyncio.to_thread(match_app, name)
        target = candidates[0] if candidates else name
        ok, out = await self.run_shell(["open", "-a", target])
        if not ok and candidates and target != name:
            ok, out = await self.run_shell(["open", "-a", name])
            target = name
        if not ok:
            hint = " list_applications bilan mavjud ilovalarni ko'ring." if not candidates else ""
            return False, f"'{name}' ilovasi topilmadi yoki ochilmadi: {out}.{hint}"
        others = [c for c in candidates[1:4] if c != target]
        suffix = f" (boshqa mosliklar: {', '.join(others)})" if others else ""
        return True, f"{target} ochildi{suffix}"

    async def list_applications(self, filter_text: str | None = None) -> Result:
        apps = await asyncio.to_thread(installed_apps)
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
        if name.lower() in {"finder", "nexus", "system events"}:
            return False, f"{name} ni yopish mumkin emas"
        ok, out = await self.run_applescript(f"tell application {_as_str(name)} to quit")
        if not ok:
            return False, f"{name} ni yopib bo'lmadi: {out}"
        return True, f"{name} yopildi"

    async def hide_all_windows(self) -> Result:
        script = (
            'tell application "System Events"\n'
            '  set visible of (every process whose visible is true and name is not "Finder") to false\n'
            "end tell"
        )
        ok, out = await self.run_applescript(script)
        return (True, "Barcha oynalar yashirildi") if ok else (False, f"Oynalarni yashirib bo'lmadi: {out}")

    async def list_running_apps(self) -> Result:
        script = (
            'tell application "System Events"\n'
            "  set names to name of every process whose background only is false\n"
            '  set AppleScript\'s text item delimiters to ", "\n'
            "  return names as text\n"
            "end tell"
        )
        ok, out = await self.run_applescript(script)
        if not ok:
            return False, f"Ilovalar ro'yxatini olib bo'lmadi: {out}"
        return True, f"Ishlayotgan ilovalar: {out}"

    async def frontmost_app(self) -> Result:
        ok, out = await self.run_applescript(
            'tell application "System Events" to get name of first process whose frontmost is true'
        )
        return (True, out.strip()) if ok else (False, f"Faol ilovani aniqlab bo'lmadi: {out}")

    async def is_terminal_frontmost(self) -> bool:
        """Old oynadagi ilova terminal (Terminal/iTerm/Warp/...) bo'lsa True."""
        try:
            ok, name = await asyncio.wait_for(self.frontmost_app(), timeout=5)
        except (TimeoutError, asyncio.CancelledError):
            return False
        return ok and is_terminal_app(name)

    # -- Finder ------------------------------------------------------------
    async def open_folder(self, path: str) -> Result:
        p = Path(os.path.expanduser((path or "").strip() or "~"))
        if not p.exists():
            return False, f"Papka topilmadi: {p}"
        if not p.is_dir():
            return False, f"Bu papka emas: {p}"
        ok, out = await self.run_shell(["open", str(p)])
        return (True, f"Papka ochildi: {p}") if ok else (False, f"Papkani ochib bo'lmadi: {out}")

    async def open_path(self, path: str) -> Result:
        raw = (path or "").strip()
        if not raw:
            return False, "Yo'l bo'sh"
        if re.match(r"^[a-z][a-z0-9+.-]*://", raw, re.IGNORECASE):
            ok, out = await self.run_shell(["open", raw])
            return (True, f"Ochildi: {raw}") if ok else (False, f"Ochib bo'lmadi: {out}")
        p = Path(os.path.expanduser(raw))
        if not p.exists():
            return False, f"Fayl yoki papka topilmadi: {p}"
        ok, out = await self.run_shell(["open", str(p)])
        return (True, f"Ochildi: {p}") if ok else (False, f"Ochib bo'lmadi: {out}")

    async def empty_trash(self) -> Result:
        ok, out = await self.run_applescript('tell application "Finder" to empty trash', timeout=60)
        return (True, "Savat tozalandi") if ok else (False, f"Savatni tozalab bo'lmadi: {out}")

    # -- tizim -------------------------------------------------------------
    async def lock_screen(self) -> Result:
        ok, out = await self.run_applescript(
            'tell application "System Events" to keystroke "q" using {command down, control down}'
        )
        if ok:
            return True, "Ekran qulflandi"
        cgsession = "/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession"
        if os.path.exists(cgsession):
            ok2, out2 = await self.run_shell([cgsession, "-suspend"])
            if ok2:
                return True, "Ekran qulflandi"
            out = out2
        return False, f"Ekranni qulflab bo'lmadi (Accessibility ruxsati kerak): {out}"

    async def sleep_display(self) -> Result:
        ok, out = await self.run_shell(["pmset", "displaysleepnow"])
        return (True, "Ekran uxlatildi") if ok else (False, f"Ekranni uxlatib bo'lmadi: {out}")

    async def send_notification(self, title: str, message: str) -> Result:
        title = (title or "Nexus").strip()
        message = (message or "").strip()
        script = f"display notification {_as_str(message)} with title {_as_str(title)}"
        ok, out = await self.run_applescript(script)
        return (
            (True, f"Bildirishnoma yuborildi: {title}")
            if ok
            else (False, f"Bildirishnoma yuborilmadi: {out}")
        )

    async def say_text(self, text: str, voice: str | None = None) -> Result:
        text = (text or "").strip()
        if not text:
            return False, "Matn bo'sh"
        argv = ["say"]
        if voice:
            argv += ["-v", voice]
        argv.append(text[:1000])
        timeout = min(120.0, 10.0 + len(text) / 8)
        ok, out = await self.run_shell(argv, timeout=timeout)
        return (True, "Matn o'qib berildi") if ok else (False, f"O'qib bo'lmadi: {out}")

    async def toggle_dark_mode(self) -> Result:
        script = (
            'tell application "System Events"\n'
            "  tell appearance preferences\n"
            "    set dark mode to not dark mode\n"
            "    return dark mode\n"
            "  end tell\n"
            "end tell"
        )
        ok, out = await self.run_applescript(script)
        if not ok:
            return False, f"Rejimni almashtirib bo'lmadi: {out}"
        return True, "Qorong'u rejim yoqildi" if out.strip() == "true" else "Yorug' rejim yoqildi"

    async def set_do_not_disturb(self, on: bool = True) -> Result:
        """macOS 12+ da DND uchun ochiq API yo'q. Foydalanuvchi yaratgan Shortcuts ishlatiladi.

        Muhit o'zgaruvchilari: DND_SHORTCUT_ON (standart "Nexus DND On"), DND_SHORTCUT_OFF ("Nexus DND Off").
        """
        name = (
            os.getenv("DND_SHORTCUT_ON", "Nexus DND On")
            if on
            else os.getenv("DND_SHORTCUT_OFF", "Nexus DND Off")
        )
        ok, listing = await self.run_shell(["shortcuts", "list"])
        if not ok:
            return False, f"Shortcuts ilovasi bilan bog'lanib bo'lmadi: {listing}"
        names = {line.strip() for line in listing.splitlines()}
        if name not in names:
            msg = (
                f"Bezovta qilmaslik rejimini boshqarish uchun Shortcuts ilovasida '{name}' nomli "
                "yorliq yarating (Focus → Bezovta qilmang ni yoqadigan/o'chiradigan amal bilan)."
            )
            return False, msg
        ok, out = await self.run_shell(["shortcuts", "run", name], timeout=20)
        if not ok:
            return False, f"'{name}' yorlig'i ishlamadi: {out}"
        return True, "Bezovta qilmaslik rejimi yoqildi" if on else "Bezovta qilmaslik rejimi o'chirildi"

    async def _clipboard_read(self) -> Result:
        return await run_shell(["pbpaste"])

    async def _clipboard_write(self, text: str) -> Result:
        return await run_shell(["pbcopy"], stdin=(text or "").encode("utf-8"))

    async def get_clipboard(self) -> Result:
        ok, out = await self._clipboard_read()
        if not ok:
            return False, f"Buferni o'qib bo'lmadi: {out}"
        return True, _truncate(redact_secrets(out)) if out else "Bufer bo'sh"

    async def set_clipboard(self, text: str) -> Result:
        ok, out = await self._clipboard_write(text or "")
        return (True, "Matn buferga nusxalandi") if ok else (False, f"Buferga yozib bo'lmadi: {out}")

    async def type_text(self, text: str, press_enter: bool = False) -> Result:
        """Faol oynaga matn kiritadi: bufer + Cmd+V (keystroke o'zbek/kirill matnni buzadi).

        Eski bufer saqlanadi va terishdan keyin qaytariladi.
        """
        if not text:
            return False, "Matn bo'sh"
        text = text[:5000]
        had_prev, previous = await self._clipboard_read()
        ok, out = await self._clipboard_write(text)
        if not ok:
            return False, f"Buferga yozib bo'lmadi: {out}"
        await asyncio.sleep(0.15)  # pasteboard o'rnashsin
        script = 'tell application "System Events" to keystroke "v" using command down'
        ok, out = await self.run_applescript(script)
        typed = ok
        if ok:
            await asyncio.sleep(0.4)  # paste asinxron — ilova buferni o'qib ulgursin
            if press_enter:
                ok, out = await self.run_applescript('tell application "System Events" to key code 36')
                await asyncio.sleep(0.1)
        if had_prev and previous:
            with _suppress():
                await self._clipboard_write(previous)
        if not typed:
            return False, f"Matnni terib bo'lmadi (Accessibility kerak): {out}"
        if press_enter and not ok:
            return False, f"Matn terildi, lekin Enter bosilmadi: {out}"
        msg = f"Matn terildi ({len(text)} belgi)"
        return True, msg + (" va Enter bosildi" if press_enter else "")

    @staticmethod
    def build_hotkey_script(keys: str) -> tuple[str | None, str]:
        """'cmd+shift+4' → AppleScript. `(script, xato)` qaytaradi."""
        parts = [p.strip().lower() for p in re.split(r"[+\-\s]+", (keys or "").strip()) if p.strip()]
        if not parts:
            return None, "Klavishlar kombinatsiyasi bo'sh"
        mods: list[str] = []
        key: str | None = None
        for p in parts:
            if p in _HOTKEY_MODIFIERS:
                m = _HOTKEY_MODIFIERS[p]
                if m not in mods:
                    mods.append(m)
            elif key is None:
                key = p
            else:
                return None, f"Bir nechta asosiy klavish: {key}, {p}"
        if key is None:
            return None, "Asosiy klavish ko'rsatilmagan (masalan cmd+c)"
        using = f" using {{{', '.join(mods)}}}" if mods else ""
        if key in _HOTKEY_KEYCODES:
            action = f"key code {_HOTKEY_KEYCODES[key]}{using}"
        elif len(key) == 1:
            action = f"keystroke {_as_str(key)}{using}"
        else:
            return None, f"Noma'lum klavish: {key}"
        return f'tell application "System Events" to {action}', ""

    async def press_hotkey(self, keys: str) -> Result:
        script, err = self.build_hotkey_script(keys)
        if script is None:
            return False, err
        ok, out = await self.run_applescript(script)
        return (
            (True, f"Bosildi: {keys}")
            if ok
            else (False, f"Klavishlarni bosib bo'lmadi (Accessibility kerak): {out}")
        )

    async def take_screenshot(self, target_path: str | None = None) -> Result:
        if target_path:
            path = Path(os.path.expanduser(target_path))
        else:
            stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
            path = Path(settings.screenshot_dir) / f"nexus_{stamp}.png"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"Papka yaratib bo'lmadi: {e}"
        ok, out = await self.run_shell(["screencapture", "-x", str(path)])
        if not ok or not path.exists():
            return False, f"Skrinshot olinmadi (Screen Recording ruxsati kerak): {out}"
        return True, f"Skrinshot saqlandi: {path}"

    # -- tizim ma'lumotlari ------------------------------------------------
    async def _wifi_ssid(self) -> str | None:
        """SSID ni aniqlaydi. macOS 14+ da Location Services ruxsatisiz SSID `<redacted>` bo'ladi → None."""
        iface = await self._wifi_interface()
        ok, out = await self.run_shell(["ipconfig", "getsummary", iface], timeout=5)
        if ok:
            m = re.search(r"^\s*SSID\s*:\s*(.+?)\s*$", out, re.MULTILINE)
            if m and m.group(1) and m.group(1) != "<redacted>":
                return m.group(1)
        ok, out = await self.run_shell(
            ["system_profiler", "SPAirPortDataType", "-detailLevel", "basic"], timeout=12
        )
        if ok:
            lines = out.splitlines()
            for i, line in enumerate(lines):
                if "Current Network Information" in line:
                    for nxt in lines[i + 1 : i + 4]:
                        s = nxt.strip()
                        if s.endswith(":") and len(s) > 1 and s[:-1] != "<redacted>":
                            return s[:-1]
                    break
        return None

    async def _wifi_interface(self) -> str:
        ok, out = await self.run_shell(["networksetup", "-listallhardwareports"], timeout=5)
        if ok:
            block = re.search(r"Hardware Port:\s*Wi-Fi\s*\nDevice:\s*(\S+)", out)
            if block:
                return block.group(1)
        return "en0"

    async def get_system_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "hostname": platform.node(),
            "macos_version": platform.mac_ver()[0] or platform.release(),
            "cpu_percent": None,
            "ram_percent": None,
            "ram_used_gb": None,
            "ram_total_gb": None,
            "battery_percent": None,
            "battery_charging": None,
            "wifi_ssid": None,
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
            du = shutil.disk_usage("/")
            info["disk_free_gb"] = round(du.free / 1e9, 1)
            info["disk_total_gb"] = round(du.total / 1e9, 1)
        except OSError:
            pass
        try:
            info["wifi_ssid"] = await self._wifi_ssid()
        except Exception as e:  # noqa: BLE001
            log.debug("SSID aniqlanmadi: %s", e)
        info["summary"] = _summarize_info(info)
        return info

    # -- terminal ----------------------------------------------------------
    async def run_terminal_command(self, command: str, confirmed: bool = False) -> Result:
        """Buyruqni qo'riqchi orqali bajaradi.

        `confirmed=True` — registry foydalanuvchi tasdig'ini olgan ("confirm" hukmi uchun).
        Tasdiqsiz "confirm" buyruq bajarilmaydi.
        """
        if not settings.allow_terminal:
            return False, "Terminal buyruqlari sozlamalarda o'chirilgan (ALLOW_TERMINAL=false)"
        verdict, reason = self.guard.check(command)
        if verdict == "deny":
            return False, f"Buyruq rad etildi: {reason}"
        if verdict == "confirm" and not confirmed:
            return False, f"Tasdiq kerak: {reason}"
        argv = CommandGuard.argv(command)
        ok, out = await self.run_shell(argv, timeout=15)
        out = _truncate(redact_secrets(out), MAX_OUTPUT_CHARS)
        if ok:
            return True, out or "(chiqish bo'sh)"
        return False, out or "Buyruq xato bilan tugadi"

    # -- ruxsatlar ---------------------------------------------------------
    async def check_permissions(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "accessibility": None,
            "screen_recording": None,
            "automation_system_events": None,
            "microphone": None,
            "hints": [],
        }
        try:
            ax = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
            )
            ax.AXIsProcessTrusted.restype = ctypes.c_bool
            result["accessibility"] = bool(ax.AXIsProcessTrusted())
        except (OSError, AttributeError):
            pass
        try:
            cg = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
            cg.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
            result["screen_recording"] = bool(cg.CGPreflightScreenCaptureAccess())
        except (OSError, AttributeError):
            pass
        ok, _ = await self.run_applescript(
            'tell application "System Events" to get name of first process', timeout=8
        )
        result["automation_system_events"] = ok
        try:
            import AVFoundation  # type: ignore

            status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_("soun")
            result["microphone"] = status == 3  # AVAuthorizationStatusAuthorized
        except Exception:  # noqa: BLE001
            result["microphone"] = None

        hints = result["hints"]
        if result["accessibility"] is False:
            hints.append(
                "Accessibility ruxsati yo'q: System Settings → Privacy & Security → Accessibility "
                "bo'limida Terminal/Python ga ruxsat bering (klavish bosish, matn terish uchun kerak)."
            )
        if result["screen_recording"] is False:
            hints.append(
                "Screen Recording ruxsati yo'q: Privacy & Security → Screen & System Audio Recording "
                "(skrinshot uchun kerak)."
            )
        if result["automation_system_events"] is False:
            hints.append(
                "Automation ruxsati yo'q: Privacy & Security → Automation bo'limida System Events ga ruxsat bering."
            )
        if result["microphone"] is None:
            hints.append(
                "Mikrofon holatini avtomatik tekshirib bo'lmadi: Privacy & Security → Microphone ni tekshiring."
            )
        elif result["microphone"] is False:
            hints.append("Mikrofon ruxsati yo'q: Privacy & Security → Microphone.")
        result["message"] = " ".join(hints) if hints else "Barcha kerakli ruxsatlar mavjud ko'rinadi."
        return result


def _fmt_uptime(secs: int) -> str:
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    parts = []
    if days:
        parts.append(f"{days} kun")
    if hours:
        parts.append(f"{hours} soat")
    parts.append(f"{minutes} daqiqa")
    return " ".join(parts)


def _summarize_info(info: dict[str, Any]) -> str:
    bits = []
    if info.get("cpu_percent") is not None:
        bits.append(f"CPU {info['cpu_percent']}%")
    if info.get("ram_percent") is not None:
        bits.append(f"RAM {info['ram_percent']}% ({info['ram_used_gb']}/{info['ram_total_gb']} GB)")
    if info.get("battery_percent") is not None:
        state = "quvvatlanmoqda" if info.get("battery_charging") else "batareyada"
        bits.append(f"Batareya {info['battery_percent']}% ({state})")
    if info.get("wifi_ssid"):
        bits.append(f"Wi-Fi: {info['wifi_ssid']}")
    if info.get("disk_free_gb") is not None:
        bits.append(f"Disk bo'sh: {info['disk_free_gb']} GB")
    if info.get("uptime"):
        bits.append(f"Ishlash vaqti: {info['uptime']}")
    if info.get("macos_version"):
        bits.append(f"macOS {info['macos_version']}")
    return "; ".join(bits) if bits else json.dumps(info, ensure_ascii=False)


__all__ = [
    "APP_FOLDERS",
    "TERMINAL_APPS",
    "CommandGuard",
    "MacOSController",
    "_as_str",
    "_match_app",
    "installed_apps",
    "is_terminal_app",
    "match_app",
    "run_applescript",
    "run_shell",
]
