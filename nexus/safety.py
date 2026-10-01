"""Xavfsizlik qatlami: xavfli shell naqshlari, sezgir yo'llar, sir redaktsiyasi,
og'zaki/UI tasdiq darvozasi (ConfirmationGate), taint kuzatuvi va loop guard.

Asosiy g'oya: model "foydalanuvchi rozi bo'ldi" deb aytishiga ishonilmaydi —
tasdiq foydalanuvchining O'Z transkriptidan (so'rovdan KEYIN aytilgan qisqa
"ha") yoki UI tugmasidan (`confirm` buyrug'i) olinadi.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import secrets
import shlex
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("nexus.safety")

# ---------------------------------------------------------------------------
# Xavfli shell naqshlari — mos kelsa buyruq HECH QACHON bajarilmaydi (deny)
# ---------------------------------------------------------------------------
# Buyruq pozitsiyasi: qator boshi, shell operatoridan keyin yoki sudo/exec/xargs/env/
# nohup/find -exec kabi "ishga tushiruvchi"dan keyin. `brew install wget` dagi `wget`
# paket nomi — buyruq emas, shuning uchun ilinmaydi.
_CMD_POS = r"(?:^|[|;&`(]\s*|\b(?:sudo|doas|exec|xargs|env|nohup|time|command|builtin)\s+|-exec(?:dir)?\s+)"


def _cmd(pattern: str) -> str:
    """Faqat buyruq pozitsiyasidagi nomga mos keladigan regex."""
    return _CMD_POS + r"(?:\S*/)?" + pattern + r"\b"


DANGEROUS_SHELL: list[str] = [
    # o'chirish / superuser
    _cmd(r"rm"),
    _cmd(r"rmdir"),
    _cmd(r"unlink"),
    _cmd(r"srm"),
    _cmd(r"shred"),
    _cmd(r"sudo"),
    _cmd(r"su"),
    _cmd(r"doas"),
    # disk / fayl tizimi
    _cmd(r"mkfs\S*"),
    _cmd(r"diskutil"),
    _cmd(r"fdisk"),
    _cmd(r"dd"),
    _cmd(r"truncate"),
    # tizim holati
    _cmd(r"shutdown"),
    _cmd(r"reboot"),
    _cmd(r"halt"),
    _cmd(r"poweroff"),
    _cmd(r"logout"),
    _cmd(r"killall"),
    _cmd(r"pkill"),
    _cmd(r"kill"),
    # ruxsatlar / sozlamalar / persistensiya
    _cmd(r"chmod"),
    _cmd(r"chown"),
    _cmd(r"chflags"),
    _cmd(r"defaults\s+(?:write|delete)"),
    _cmd(r"launchctl"),
    _cmd(r"systemsetup"),
    _cmd(r"csrutil"),
    _cmd(r"spctl"),
    _cmd(r"nvram"),
    _cmd(r"tccutil"),
    _cmd(r"crontab"),
    _cmd(r"at") + r"\s",
    _cmd(r"ln") + r"\s",
    _cmd(r"tee"),
    # versiya nazorati / paketlar — qaytarib bo'lmaydigan amallar
    _cmd(r"git\s+(?:push|reset\s+--hard|clean|checkout\s+--)"),
    _cmd(r"npm\s+publish"),
    _cmd(r"pip3?\s+uninstall"),
    _cmd(r"brew\s+uninstall"),
    # interpretatorga quvur (pipe) — istalgan tartibda
    r"\|\s*(?:ba|z|k)?sh\b",
    r"\|\s*python[0-9.]*\b",
    r"\|\s*node\b",
    r"\|\s*perl\b",
    r"\|\s*ruby\b",
    # kodlash / yashirish
    _cmd(r"base64"),
    _cmd(r"xxd"),
    # tarmoqdan yuklab faylga yozish / uzatish
    _cmd(r"curl") + r".*\s-[a-zA-Z]*[oO]\b",
    _cmd(r"curl") + r".*--output\b",
    _cmd(r"curl") + r".*--remote-name\b",
    _cmd(r"wget"),
    _cmd(r"ftp"),
    _cmd(r"sftp"),
    _cmd(r"scp"),
    _cmd(r"nc") + r"\s",
    _cmd(r"ncat"),
    # interpretator bir qatorliklari — ixtiyoriy kod
    _cmd(r"python[0-9.]*") + r".*\s-c\b",
    _cmd(r"perl") + r".*\s-e\b",
    _cmd(r"ruby") + r".*\s-e\b",
    _cmd(r"node") + r".*\s-e\b",
    _cmd(r"osascript"),
    _cmd(r"eval"),
    _cmd(r"exec"),
    # yo'naltirish (redirect) — faylga yozadi
    r">\s*[^\s&|;]",
    r">>\s*[^\s&|;]",
    # mv … / (ildiz yoki yuqori darajali papkaga ko'chirish)
    _cmd(r"mv") + r".*\s/(?:[^/\s]*/?)?\s*$",
]
_DANGEROUS_RE = re.compile("|".join(DANGEROUS_SHELL), re.IGNORECASE)


def shell_is_dangerous(command: str) -> bool:
    """True — buyruq DANGEROUS_SHELL naqshlaridan biriga mos keladi."""
    return bool(command) and bool(_DANGEROUS_RE.search(command))


# ---------------------------------------------------------------------------
# Faqat o'qiydigan buyruqlar (tez yo'l)
# ---------------------------------------------------------------------------
# ATAYIN yo'q: sort (-o yozadi), awk (system()), sed (w), env/xargs (dastur ishga
# tushiradi), find (-exec/-delete), tr. Ular to'liq tekshiruvdan o'tadi.
READ_ONLY_COMMANDS = frozenset(
    {
        "ls",
        "cat",
        "head",
        "tail",
        "echo",
        "date",
        "pwd",
        "whoami",
        "id",
        "uname",
        "which",
        "type",
        "wc",
        "stat",
        "file",
        "du",
        "df",
        "ps",
        "uptime",
        "hostname",
        "sw_vers",
        "locale",
        "basename",
        "dirname",
        "realpath",
        "readlink",
        "uniq",
        "cut",
        "grep",
        "egrep",
        "fgrep",
        "diff",
        "cmp",
        "md5",
        "shasum",
        "cal",
        "printf",
    }
)
_GIT_READ_ONLY = frozenset({"status", "log", "diff", "show", "branch", "--version"})
_NOT_READ_ONLY = re.compile(
    r"[>|;&`\n]"  # yo'naltirish, quvur, zanjir, backtick, yangi qator
    r"|\$\("  # buyruq almashtirish
    r"|(?<![\w-])-o(?![\w-])"  # yalang'och -o (chiqish fayli)
    r"|--output\b"
)


def looks_read_only(command: str) -> bool:
    """True — buyruq HECH QANDAY bayroq bilan ham hech narsani o'zgartira olmaydi."""
    text = (command or "").strip()
    if not text or _NOT_READ_ONLY.search(text):
        return False
    try:
        words = shlex.split(text)
    except ValueError:
        return False
    if not words:
        return False
    first = words[0].rsplit("/", 1)[-1]
    if first == "git":
        return len(words) > 1 and words[1] in _GIT_READ_ONLY
    return first in READ_ONLY_COMMANDS


# ---------------------------------------------------------------------------
# Sezgir yo'llar
# ---------------------------------------------------------------------------
_SENSITIVE_NAMES = frozenset(
    {
        ".zshrc",
        ".zprofile",
        ".zshenv",
        ".zlogin",
        ".bashrc",
        ".bash_profile",
        ".bash_login",
        ".profile",
        ".netrc",
        ".pgpass",
        ".env",
        "authorized_keys",
        "known_hosts",
        "id_rsa",
        "id_ed25519",
        "crontab",
        "sudoers",
        "hosts",
    }
)
_SENSITIVE_DIRS = (
    "/.ssh",
    "/.gnupg",
    "/.aws",
    "/library/launchagents",
    "/library/launchdaemons",
    "/library/preferences",
    "/library/keychains",
    "/system",
    "/etc",
    "/private/etc",
    "/usr/bin",
    "/usr/sbin",
    "/usr/lib",
    "/usr/local/bin",
    "/bin",
    "/sbin",
    "/var/db",
    "/.config/autostart",
    # Windows: avtoyuklash, tizim va dasturlar papkalari
    "/start menu/programs/startup",
    "c:/windows",
    "c:/program files",
    "c:/program files (x86)",
    "c:/programdata",
)
_SENSITIVE_SUFFIXES = (
    ".plist", ".command", ".sh", ".zsh", ".bash", ".terminal", ".workflow", ".app",
    # Windows: ishga tushadigan skript/yorliq/registr fayllari
    ".bat", ".cmd", ".ps1", ".vbs", ".lnk", ".reg", ".scr",
)


def path_is_sensitive(path: str | Path | None) -> bool:
    """True — bu yerga yozish persistensiya yaratishi yoki sir sizdirishi mumkin."""
    if path is None or not str(path).strip():
        return True
    try:
        resolved = Path(str(path)).expanduser().resolve()
    except (OSError, RuntimeError):
        return True
    lowered = str(resolved).lower().replace("\\", "/")  # Windows yo'llari ham "/" bilan solishtiriladi
    name = resolved.name
    if name in _SENSITIVE_NAMES:
        return True
    home = Path.home()
    if name.startswith(".") and (resolved.parent == home or resolved == home):
        return True  # uy papkasidagi istalgan dotfile
    for part in resolved.parts:
        if part.startswith(".") and part in {".ssh", ".gnupg", ".aws", ".config", ".docker", ".kube"}:
            return True
    for d in _SENSITIVE_DIRS:
        if lowered == d or lowered.startswith(d + "/") or (lowered + "/").find(d + "/") >= 0:
            return True
    return resolved.suffix.lower() in _SENSITIVE_SUFFIXES


# ---------------------------------------------------------------------------
# Sirlarni redaktsiya qilish
# ---------------------------------------------------------------------------
_SECRET_ASSIGN = re.compile(
    r"((?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AUTH|BEARER|"
    r"PRIVATE[_-]?KEY|ACCESS[_-]?KEY|CLIENT[_-]?SECRET)\w*\s*[=:]\s*[\"']?)((?:Bearer\s+)?[^\s\"',;]{6,})",
    re.IGNORECASE,
)
_SECRET_TOKEN = re.compile(
    r"(?<![A-Za-z0-9_])(sk-[A-Za-z0-9_-]{12,}|AQ\.[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}|"
    r"apikey_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"
)
_BEARER = re.compile(r"(\bBearer\s+)([A-Za-z0-9._~+/=-]{8,})", re.IGNORECASE)
REDACTED = "***REDACTED***"


def redact_secrets(text: str) -> str:
    """Model yoki log ko'rishidan oldin kalitga o'xshagan narsalarni yashiradi."""
    if not text:
        return text
    text = _SECRET_ASSIGN.sub(lambda m: m.group(1) + REDACTED, text)
    text = _BEARER.sub(lambda m: m.group(1) + REDACTED, text)
    text = _SECRET_TOKEN.sub(REDACTED, text)
    return text


# ---------------------------------------------------------------------------
# Tasdiq darvozasi
# ---------------------------------------------------------------------------
AFFIRMATIVE = re.compile(
    r"(?<!\w)(ha|xa|mayli|bo'?ladi|boladi|bo'?lsin|bolsin|davom\s*et|tasdiqla|tasdiqlayman|roziman|"
    r"yes|confirm|да|давай|подтверждаю)(?!\w)",
    re.IGNORECASE,
)
NEGATIVE = re.compile(
    r"(?<!\w)(yo'?q|yoq|kerak\s*emas|bekor|to'?xta|toxta|no|cancel|нет|отмена)(?!\w)",
    re.IGNORECASE,
)
MAX_AFFIRMATIVE_WORDS = 6
DEFAULT_CONFIRM_TTL = 60.0


def spoken_verdict(text: str) -> bool | None:
    """True = rozi, False = rad, None = javob emas.

    Rad etish (veto) gap uzunligidan qat'i nazar hisobga olinadi; rozilik esa
    faqat QISQA gapda (≤6 so'z) — "ha, shunaqa gaplar bor edi" rozilik emas.
    """
    t = (text or "").strip()
    if not t:
        return None
    if NEGATIVE.search(t):
        return False
    words = [w for w in re.split(r"\s+", t) if w]
    if len(words) <= MAX_AFFIRMATIVE_WORDS and AFFIRMATIVE.search(t):
        return True
    return None


@dataclass
class PendingConfirmation:
    token: str
    action: str
    summary: str
    reason: str
    ttl_s: float
    requested_at: float = field(default_factory=time.time)
    event: asyncio.Event = field(default_factory=asyncio.Event)
    approved: bool | None = None
    source: str | None = None

    @property
    def resolved(self) -> bool:
        return self.approved is not None

    @property
    def expired(self) -> bool:
        return time.time() - self.requested_at > self.ttl_s


class ConfirmationGate:
    """Bir vaqtda faqat bitta faol tasdiq so'rovi. Yangi so'rov eskisini bekor qiladi."""

    def __init__(self, bus: Any = None, ttl_s: float = DEFAULT_CONFIRM_TTL) -> None:
        self.bus = bus
        self.ttl_s = float(ttl_s)
        self._pending: PendingConfirmation | None = None
        self._history: list[PendingConfirmation] = []
        self._listener: asyncio.Task | None = None
        if bus is not None:
            bus.register_command("confirm", self._cmd_confirm)

    # -- holat ------------------------------------------------------------
    @property
    def pending(self) -> PendingConfirmation | None:
        p = self._pending
        if p is not None and not p.resolved and p.expired:
            self.resolve(p.token, False, "timeout")
            return None
        return p if (p is not None and not p.resolved) else None

    # -- so'rov -----------------------------------------------------------
    def request(self, action: str, summary: str, reason: str = "", ttl_s: float | None = None) -> str:
        ttl = float(ttl_s) if ttl_s else self.ttl_s
        old = self._pending
        if old is not None and not old.resolved:
            self.resolve(old.token, False, "cancelled")
        token = secrets.token_hex(3)
        p = PendingConfirmation(token=token, action=action, summary=summary, reason=reason, ttl_s=ttl)
        self._pending = p
        self._publish(
            "CONFIRM_REQUEST",
            {"token": token, "action": action, "summary": summary, "reason": reason, "ttl_s": int(ttl)},
        )
        self._set_state("awaiting_confirmation")
        log.info("Tasdiq so'raldi [%s] %s: %s", token, action, summary)
        return token

    def resolve(self, token: str, approved: bool, source: str = "ui") -> bool:
        p = self._pending
        if p is None or p.token != token or p.resolved:
            return False
        p.approved = bool(approved)
        p.source = source
        p.event.set()
        self._history.append(p)
        del self._history[:-20]
        self._publish("CONFIRM_RESOLVED", {"token": token, "approved": p.approved, "source": source})
        if self.bus is not None and getattr(self.bus, "state", None) == "awaiting_confirmation":
            self._set_state("tool_executing" if p.approved else "processing")
        log.info("Tasdiq [%s] %s (%s)", token, "qabul" if p.approved else "rad", source)
        return True

    def cancel_pending(self, source: str = "cancelled") -> bool:
        p = self._pending
        if p is None or p.resolved:
            return False
        return self.resolve(p.token, False, source)

    async def wait(self, token: str, timeout: float | None = None) -> bool:
        p = self._pending
        if p is None or p.token != token:
            return False
        if p.resolved:
            return bool(p.approved)
        self._ensure_listener()
        remaining = p.ttl_s - (time.time() - p.requested_at)
        if timeout is not None:
            remaining = min(remaining, float(timeout))
        try:
            await asyncio.wait_for(p.event.wait(), timeout=max(0.0, remaining))
        except TimeoutError:
            self.resolve(token, False, "timeout")
            return False
        return bool(p.approved)

    # -- og'zaki tasdiq ----------------------------------------------------
    def note_utterance(self, text: str, ts: float | None = None) -> bool | None:
        """Foydalanuvchining yakuniy transkripti. So'rovdan OLDIN aytilgan gap hisobga olinmaydi."""
        p = self.pending
        if p is None:
            return None
        stamp = time.time() if ts is None else float(ts)
        if stamp < p.requested_at:
            return None
        verdict = spoken_verdict(text)
        if verdict is None:
            return None
        self.resolve(p.token, verdict, "voice")
        return verdict

    def _ensure_listener(self) -> None:
        """Bus'dagi TRANSCRIPT (user, final) hodisalarini ham kuzatadi — gemini client
        `note_utterance` ni chaqirmasa ham og'zaki tasdiq ishlaydi."""
        if self.bus is None or not hasattr(self.bus, "subscribe"):
            return
        if self._listener is not None and not self._listener.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        q = self.bus.subscribe()

        async def _consume() -> None:
            try:
                while True:
                    ev = await q.get()
                    if ev.get("type") != "TRANSCRIPT":
                        continue
                    d = ev.get("data") or {}
                    if d.get("role") == "user" and d.get("final"):
                        self.note_utterance(str(d.get("text") or ""), float(ev.get("ts") or time.time()))
            finally:
                self.bus.unsubscribe(q)

        self._listener = loop.create_task(_consume(), name="confirm-listener")

    # -- UI buyrug'i --------------------------------------------------------
    async def _cmd_confirm(self, msg: dict[str, Any]) -> dict[str, Any]:
        token = str(msg.get("token") or "")
        approve = msg.get("approve", msg.get("value", False))
        if isinstance(approve, str):
            approve = approve.strip().lower() in {"1", "true", "yes", "ha", "on"}
        p = self.pending
        if not token and p is not None:
            token = p.token
        ok = self.resolve(token, bool(approve), "ui")
        if not ok:
            return {"resolved": False, "error": "Faol tasdiq so'rovi yo'q yoki token noto'g'ri"}
        return {"resolved": True, "token": token, "approved": bool(approve)}

    # -- yordamchilar --------------------------------------------------------
    def _publish(self, type_: str, data: dict[str, Any]) -> None:
        if self.bus is None:
            return
        try:
            self.bus.publish(type_, data)
        except Exception:
            log.exception("%s nashr qilinmadi", type_)

    def _set_state(self, state: str) -> None:
        if self.bus is None or not hasattr(self.bus, "set_state"):
            return
        try:
            self.bus.set_state(state)
        except Exception:  # noqa: BLE001
            log.debug("Holatni o'rnatib bo'lmadi: %s", state)


# ---------------------------------------------------------------------------
# Taint kuzatuvi (prompt injection)
# ---------------------------------------------------------------------------
# Bu toollar foydalanuvchi AYTMAGAN matnni modelga kiritadi (sahifa, fayl, bufer).
INGESTS_EXTERNAL_CONTENT = frozenset(
    {
        "browser_read_page",
        "browser_current_page",
        "search_get_results",
        "get_clipboard",
        "read_file",
        "read_spreadsheet",
        "read_screen_text",
        "list_ui_elements",
    }
)
# Tashqi matn kontekstga kirgach, bular uning "buyrug'i" bilan ma'lumot sizdirishi
# yoki kod bajarishi mumkin — shu navbatda tasdiq talab qiladi.
EXFIL_OR_EXECUTE = frozenset(
    {
        "run_terminal_command",
        "browser_open_url",
        "open_path",
        "web_search",
        "type_text",
        "press_hotkey",
        "browser_click_button",
        "browser_click_selector",
        "browser_type_and_search",
        "write_file",
        "delete_file",
        "menu_command",
        "click_ui_element",
    }
)


class TaintTracker:
    """Navbat ichida tashqi matn o'qilganini eslab qoladi."""

    def __init__(self) -> None:
        self.tainted = False
        self.sources: list[str] = []

    def new_turn(self) -> None:
        self.tainted = False
        self.sources = []

    def after(self, name: str) -> None:
        if name in INGESTS_EXTERNAL_CONTENT:
            self.tainted = True
            if name not in self.sources:
                self.sources.append(name)

    def requires_confirmation(self, name: str) -> bool:
        return self.tainted and name in EXFIL_OR_EXECUTE

    def reason(self, name: str) -> str:
        src = ", ".join(self.sources) or "tashqi matn"
        return f"{name} — shu navbatda tashqi matn o'qilgan ({src}); prompt injection ehtimoli"


# ---------------------------------------------------------------------------
# Loop guard
# ---------------------------------------------------------------------------
MAX_CALLS_PER_TURN = 15
MAX_IDENTICAL_CALLS = 3


class LoopGuard:
    """Bir navbatda haddan ko'p yoki bir xil chaqiruvlarni to'xtatadi."""

    def __init__(self, max_calls: int = MAX_CALLS_PER_TURN, max_identical: int = MAX_IDENTICAL_CALLS) -> None:
        self.max_calls = int(max_calls)
        self.max_identical = int(max_identical)
        self.calls = 0
        self._seen: Counter[str] = Counter()

    def new_turn(self) -> None:
        self.calls = 0
        self._seen = Counter()

    @staticmethod
    def signature(name: str, args: dict[str, Any] | None) -> str:
        try:
            body = json.dumps(args or {}, sort_keys=True, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            body = repr(args)
        return f"{name}:{body}"

    def check(self, name: str, args: dict[str, Any] | None) -> str | None:
        """None — davom et; matn — rad etish sababi (modelga tushuntirish)."""
        sig = self.signature(name, args)
        self._seen[sig] += 1
        self.calls += 1
        n = self._seen[sig]
        if n > self.max_identical:
            log.warning("loop guard: %s bir xil argumentlar bilan %d marta", name, n)
            return (
                f"loop guard: {name} bir xil argumentlar bilan {n} marta chaqirildi va kutilgan natijani "
                "bermayapti. Yana chaqirish hech narsani o'zgartirmaydi. To'xtang va foydalanuvchiga nima "
                "qilganingiz va nima ishlamaganini qisqa ayting."
            )
        if self.calls > self.max_calls:
            log.warning("loop guard: bir navbatda %d ta chaqiruv", self.calls)
            return (
                f"loop guard: bitta so'rov uchun {self.calls} ta amal — juda ko'p. Shu yerda to'xtang va "
                "foydalanuvchiga hozirgacha nima qilinganini va nima qolganini ayting."
            )
        return None


__all__ = [
    "AFFIRMATIVE",
    "DANGEROUS_SHELL",
    "DEFAULT_CONFIRM_TTL",
    "EXFIL_OR_EXECUTE",
    "INGESTS_EXTERNAL_CONTENT",
    "MAX_CALLS_PER_TURN",
    "MAX_IDENTICAL_CALLS",
    "NEGATIVE",
    "READ_ONLY_COMMANDS",
    "ConfirmationGate",
    "LoopGuard",
    "PendingConfirmation",
    "TaintTracker",
    "looks_read_only",
    "path_is_sensitive",
    "redact_secrets",
    "shell_is_dangerous",
    "spoken_verdict",
]
