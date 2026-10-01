"""Windows klaviatura kiritishi: `SendInput` (user32) orqali.

- `type_unicode` — matnni KEYEVENTF_UNICODE bilan teradi: klaviatura tartibiga bog'liq emas,
  o'zbek (oʻ, gʻ), kirill va emoji buzilmaydi, bufer ishlatilmaydi.
- `press_combo` — "ctrl+shift+s" kabi kombinatsiya. macOS nomlari ham qabul qilinadi
  (`cmd` → Ctrl, `option` → Alt), shuning uchun model bir xil yozuvdan foydalanadi.

Parsing (`parse_hotkey`) OS'ga bog'liq emas va macOS'da ham testlanadi; `SendInput`
chaqiruvlari faqat Windows'da bajariladi.
"""

from __future__ import annotations

import ctypes
import re
import sys
from ctypes import wintypes

INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B
VK_RETURN = 0x0D

MODIFIERS: dict[str, int] = {
    "ctrl": VK_CONTROL,
    "control": VK_CONTROL,
    # macOS yozuvi: Windows'da Cmd vazifasini Ctrl bajaradi (cmd+c → ctrl+c)
    "cmd": VK_CONTROL,
    "command": VK_CONTROL,
    "meta": VK_CONTROL,
    "shift": VK_SHIFT,
    "alt": VK_MENU,
    "option": VK_MENU,
    "opt": VK_MENU,
    "win": VK_LWIN,
    "windows": VK_LWIN,
    "super": VK_LWIN,
}

NAMED_KEYS: dict[str, int] = {
    "enter": 0x0D,
    "return": 0x0D,
    "tab": 0x09,
    "space": 0x20,
    # macOS'dagi "delete" — orqaga o'chirish (Backspace)
    "delete": 0x08,
    "backspace": 0x08,
    "forwarddelete": 0x2E,
    "del": 0x2E,
    "insert": 0x2D,
    "esc": 0x1B,
    "escape": 0x1B,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "printscreen": 0x2C,
    **{f"f{i}": 0x6F + i for i in range(1, 25)},  # F1 = 0x70
}
# Kengaytirilgan (E0 prefiksli) klavishlar — ularsiz o'q/Home/End numpad sifatida yuboriladi
EXTENDED_KEYS = frozenset({0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, VK_LWIN})
PUNCTUATION_VK: dict[str, int] = {
    ";": 0xBA,
    "=": 0xBB,
    ",": 0xBC,
    "-": 0xBD,
    ".": 0xBE,
    "/": 0xBF,
    "`": 0xC0,
    "[": 0xDB,
    "\\": 0xDC,
    "]": 0xDD,
    "'": 0xDE,
}

MAX_TYPE_CHARS = 5000


class HotkeyError(ValueError):
    pass


def parse_hotkey(keys: str) -> tuple[list[int], int]:
    """'cmd+shift+s' → ([VK_CONTROL, VK_SHIFT], ord('S')). Xato bo'lsa `HotkeyError`."""
    raw = (keys or "").strip().lower()
    # "+" ning o'zi asosiy klavish bo'lishi mumkin emas; "-" ajratuvchi sifatida ham qabul qilinadi
    parts = [p for p in re.split(r"\s*\+\s*|\s+", raw) if p]
    if len(parts) == 1 and "-" in parts[0] and len(parts[0]) > 1:
        parts = [p for p in parts[0].split("-") if p]
    if not parts:
        raise HotkeyError("Klavishlar kombinatsiyasi bo'sh")
    mods: list[int] = []
    key: int | None = None
    key_name = ""
    for p in parts:
        if p in MODIFIERS:
            vk = MODIFIERS[p]
            if vk not in mods:
                mods.append(vk)
            continue
        if key is not None:
            raise HotkeyError(f"Bir nechta asosiy klavish: {key_name}, {p}")
        key_name = p
        if p in NAMED_KEYS:
            key = NAMED_KEYS[p]
        elif len(p) == 1 and (p.isascii() and p.isalnum()):
            key = ord(p.upper())
        elif p in PUNCTUATION_VK:
            key = PUNCTUATION_VK[p]
        else:
            raise HotkeyError(f"Noma'lum klavish: {p}")
    if key is None:
        if len(mods) == 1 and mods[0] == VK_LWIN:
            return [], VK_LWIN  # faqat "win" — Start menyusi
        raise HotkeyError("Asosiy klavish ko'rsatilmagan (masalan ctrl+c)")
    return mods, key


def text_events(text: str) -> list[tuple[int, int, int]]:
    """Matn → (vk, scan, flags) hodisalari. Yangi qator — Shift+Enter (chat'da xabar yuborilmasin)."""
    events: list[tuple[int, int, int]] = []
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for ch in text:
        if ch == "\n":
            events += [
                (VK_SHIFT, 0, 0),
                (VK_RETURN, 0, 0),
                (VK_RETURN, 0, KEYEVENTF_KEYUP),
                (VK_SHIFT, 0, KEYEVENTF_KEYUP),
            ]
            continue
        data = ch.encode("utf-16-le")
        # BMP'dan tashqari belgilar (emoji) — ikkita surrogat kod birligi
        for i in range(0, len(data), 2):
            unit = int.from_bytes(data[i : i + 2], "little")
            events.append((0, unit, KEYEVENTF_UNICODE))
            events.append((0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
    return events


def combo_events(mods: list[int], key: int) -> list[tuple[int, int, int]]:
    def flags(vk: int, up: bool) -> int:
        return (KEYEVENTF_EXTENDEDKEY if vk in EXTENDED_KEYS else 0) | (KEYEVENTF_KEYUP if up else 0)

    down = [(vk, 0, flags(vk, False)) for vk in [*mods, key]]
    up = [(vk, 0, flags(vk, True)) for vk in reversed([*mods, key])]
    return down + up


# ---------------------------------------------------------------------------
# SendInput (faqat Windows)
# ---------------------------------------------------------------------------
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class _INPUTUNION(ctypes.Union):
    # Union eng katta a'zo (MOUSEINPUT) o'lchamida bo'lishi shart — aks holda SendInput 0 qaytaradi
    _fields_ = (("ki", KEYBDINPUT), ("mi", MOUSEINPUT))


class INPUT(ctypes.Structure):
    _fields_ = (("type", wintypes.DWORD), ("u", _INPUTUNION))


def send_events(events: list[tuple[int, int, int]], chunk: int = 200) -> int:
    """Hodisalarni SendInput bilan yuboradi; yuborilganlar sonini qaytaradi."""
    if sys.platform != "win32":
        raise OSError("SendInput faqat Windows'da mavjud")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT
    sent = 0
    for start in range(0, len(events), chunk):
        part = events[start : start + chunk]
        arr = (INPUT * len(part))()
        for i, (vk, scan, flags) in enumerate(part):
            arr[i].type = INPUT_KEYBOARD
            arr[i].u.ki = KEYBDINPUT(vk, scan, flags, 0, 0)
        n = user32.SendInput(len(part), arr, ctypes.sizeof(INPUT))
        sent += n
        if n != len(part):
            err = ctypes.get_last_error()
            raise OSError(f"SendInput {n}/{len(part)} hodisani yubordi (xato {err}) — "
                          "oyna administrator huquqida ishlayotgan bo'lishi mumkin")
    return sent


def type_unicode(text: str) -> int:
    return send_events(text_events(text[:MAX_TYPE_CHARS]))


def press_combo(keys: str) -> None:
    mods, key = parse_hotkey(keys)
    send_events(combo_events(mods, key))


def press_enter() -> None:
    send_events([(VK_RETURN, 0, 0), (VK_RETURN, 0, KEYEVENTF_KEYUP)])


__all__ = [
    "HotkeyError",
    "combo_events",
    "parse_hotkey",
    "press_combo",
    "press_enter",
    "send_events",
    "text_events",
    "type_unicode",
]
