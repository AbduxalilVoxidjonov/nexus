"""macOS Accessibility (AX) toollari — kengaytma moduli.

Oldingi oynadagi boshqaruv elementlarini (tugma, havola, matn maydoni ...) rasm
emas, balki operatsion tizimning o'zidan (AX API) o'qiydi. Shu sababli pozitsiyalar
aniq: "Yangi tugmasini bos" so'rovi uchun model koordinatani taxmin qilmaydi.

Eksport (registry kontrakti):
    TOOL_DECLARATIONS: list[dict]   — Gemini FunctionDeclaration lug'atlari
    HANDLERS: dict[str, handler]    — name -> async handler(args) -> (ok, out) | dict

pyobjc (ApplicationServices, Quartz, Cocoa) o'rnatilmagan bo'lsa modul baribir
yuklanadi; har bir handler "pyobjc o'rnatilmagan" xatosini qaytaradi.

Sinxron AX yurishi (walk) `asyncio.to_thread` ichida bajariladi — audio oqimi
to'xtab qolmaydi. Chrome/Electron ilovalari veb-daraxtini faqat
`AXManualAccessibility` so'ralganda ochadi (`enable_full_tree`).
"""

from __future__ import annotations

import asyncio
import difflib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("nexus.ax")

# ---------------------------------------------------------------------------
# pyobjc mavjudligi
# ---------------------------------------------------------------------------
_IMPORT_ERROR: str | None = None
try:  # pragma: no cover - real macOS kutubxonalari
    if sys.platform != "darwin":
        raise ImportError("faqat macOS")
    import ApplicationServices as _AS  # type: ignore
    import Quartz as _QZ  # type: ignore
    from AppKit import NSWorkspace as _NSWorkspace  # type: ignore
except Exception as _e:  # noqa: BLE001
    _AS = None
    _QZ = None
    _NSWorkspace = None
    _IMPORT_ERROR = f"{type(_e).__name__}: {_e}"

PYOBJC_HINT = (
    "pyobjc o'rnatilmagan (AX toollari ishlamaydi). O'rnatish: "
    'uv pip install -e ".[dev]"  (pyobjc-framework-ApplicationServices/Quartz/Cocoa).'
)
ACCESSIBILITY_HINT = (
    "Accessibility ruxsati yo'q: System Settings → Privacy & Security → Accessibility "
    "bo'limida Terminal (yoki Python) ga ruxsat bering, so'ng Nexus'ni qayta ishga tushiring."
)

# ---------------------------------------------------------------------------
# Sozlamalar
# ---------------------------------------------------------------------------
MAX_DEPTH = 40
MAX_VISITED = 8000
LABEL_ATTRS = (
    "AXTitle",
    "AXDescription",
    "AXValue",
    "AXHelp",
    "AXLabel",
    "AXPlaceholderValue",
    "AXRoleDescription",
)
LABEL_MAX = 80
AX_TIMEOUT_S = 3.0

# Ro'yxatga kiritiladigan (bosiladigan) rollar. Konteynerlar yuriladi, lekin chiqmaydi.
ACTIONABLE = frozenset(
    {
        "AXButton",
        "AXMenuItem",
        "AXMenuBarItem",
        "AXMenuButton",
        "AXPopUpButton",
        "AXCheckBox",
        "AXRadioButton",
        "AXTextField",
        "AXTextArea",
        "AXSearchField",
        "AXLink",
        "AXCell",
        "AXRow",
        "AXTabButton",
        "AXToolbarButton",
        "AXIncrementor",
        "AXDisclosureTriangle",
        "AXColorWell",
        "AXSlider",
        "AXComboBox",
        "AXOutline",
        "AXImage",
    }
)
TEXT_ROLES = frozenset({"AXTextField", "AXTextArea", "AXSearchField", "AXComboBox"})
READABLE_ROLES = frozenset({"AXStaticText", "AXHeading", "AXLink", "AXTextArea", "AXTextField"})

# Oldingi ilova uchun AXManualAccessibility bir marta so'raladi
_ENABLED_PIDS: set[int] = set()
# Oxirgi list_ui_elements natijasi (index bo'yicha klik uchun); source: "ax" | "ocr" | "ax+ocr"
_LAST_LISTING: dict[str, Any] = {"pid": None, "items": [], "source": "ax"}

# Qt ilovalar: AX daraxti bo'sh yoki chala (Telegram faqat chat ro'yxatini beradi, xabarlarni emas).
# Ular uchun AXManualAccessibility so'ralgach 1.5 s kutiladi, baribir kam bo'lsa OCR ishlatiladi.
QT_APPS = frozenset({"telegram", "wps office", "wps", "qbittorrent", "vlc"})
QT_SETTLE_S = 1.5
# AX matni shundan qisqa bo'lsa OCR zaxirasi ishga tushadi
AX_TEXT_MIN_CHARS = 40
# AX shundan kam element bersa OCR satrlari qo'shiladi
AX_ELEMENTS_MIN = 2
OCR_NOTE = "Ilova Accessibility bermadi, OCR ishlatildi"


# ---------------------------------------------------------------------------
# Toza (pyobjc'siz) funksiyalar — testlanadi
# ---------------------------------------------------------------------------
@dataclass
class Element:
    n: int
    role: str
    label: str
    at: tuple[int, int]
    size: tuple[int, int]
    ref: Any = field(default=None, repr=False, compare=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "role": self.role.removeprefix("AX"),
            "label": self.label,
            "at": list(self.at),
            "size": list(self.size),
        }


def _clean_text(value: Any, limit: int = LABEL_MAX) -> str:
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())
    return text[:limit]


def pick_label(attrs: dict[str, Any]) -> str:
    """Attribut lug'atidan yorliqni tanlaydi (AXTitle → AXDescription → AXValue → ...).

    Bo'sh / satr bo'lmagan qiymatlar o'tkazib yuboriladi; natija 80 belgigacha qisqartiriladi.
    """
    for name in LABEL_ATTRS:
        text = _clean_text(attrs.get(name))
        if text:
            return text
    return ""


_ELLIPSIS_RE = re.compile(r"(\.{3}|…)+$")


def _norm(text: str) -> str:
    text = " ".join((text or "").lower().replace("_", " ").split())
    return _ELLIPSIS_RE.sub("", text).strip()


def _match_label(wanted: str, label: str) -> float:
    """Fuzzy moslik bahosi 0..1 (0 = mos emas).

    1.0  — aynan bir xil (registrsiz, bo'shliqlar normallashtirilgan)
    0.85 — biri ikkinchisining ichida ("save" ⊂ "save as")
    0.8  — so'ralgan so'zlarning hammasi yorliqda bor
    0.6..0.99 — difflib o'xshashligi (imlo xatolari uchun), 0.72 dan yuqori bo'lsa
    """
    w, c = _norm(wanted), _norm(label)
    if not w or not c:
        return 0.0
    if w == c:
        return 1.0
    if w in c or (len(w) >= 3 and c in w):
        return 0.85
    w_tokens = w.split()
    if len(w_tokens) > 1 and all(t in c for t in w_tokens):
        return 0.8
    ratio = difflib.SequenceMatcher(None, w, c).ratio()
    if ratio >= 0.72:
        return round(ratio * 0.99, 3)
    return 0.0


def rank_matches(
    wanted: str, elements: list[Element], min_score: float = 0.72
) -> list[tuple[float, Element]]:
    """Elementlarni moslik bahosi bo'yicha saralaydi (yuqori → past, teng bo'lsa kattaroq element oldin)."""
    scored = []
    for el in elements:
        s = _match_label(wanted, el.label)
        if s >= min_score:
            scored.append((s, el))
    scored.sort(key=lambda t: (-t[0], -(t[1].size[0] * t[1].size[1]), t[1].n))
    return scored


def _result(ok: bool, output: Any, **extra: Any) -> dict[str, Any]:
    text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
    d: dict[str, Any] = {"ok": ok, "output": text}
    d.update(extra)
    return d


def is_qt_app(app_name: str) -> bool:
    """Qt ilovasi (AX daraxti ishonchsiz) — nom bo'yicha."""
    name = (app_name or "").strip().lower()
    return bool(name) and any(name == q or name.startswith(q + " ") for q in QT_APPS)


def needs_text_fallback(app_name: str, text: str, min_chars: int = AX_TEXT_MIN_CHARS) -> bool:
    """AX matni o'rniga OCR kerakmi: matn juda qisqa yoki ilova Qt (AX faqat yon panelni beradi)."""
    return len((text or "").strip()) < min_chars or is_qt_app(app_name)


def needs_elements_fallback(app_name: str, count: int, min_items: int = AX_ELEMENTS_MIN) -> bool:
    """AX elementlar ro'yxatiga OCR satrlarini qo'shish kerakmi."""
    return count <= min_items or is_qt_app(app_name)


def ocr_elements(lines: list[dict[str, Any]], start: int = 1) -> list[Element]:
    """OCR satrlari ({text, x, y, w, h}) → Element (role 'text', ref=None — faqat Quartz klik)."""
    from nexus.screen_reader import lines_as_elements

    out: list[Element] = []
    for i, item in enumerate(lines_as_elements(lines)):
        out.append(
            Element(
                start + i,
                "text",
                item["label"],
                (int(item["at"][0]), int(item["at"][1])),
                (int(item["size"][0]), int(item["size"][1])),
            )
        )
    return out


def _ocr_read(max_chars: int = 6000) -> dict[str, Any] | None:
    """Sinxron OCR (worker thread'da). Vision yo'q yoki xato bo'lsa None."""
    try:
        from nexus import screen_reader

        if not screen_reader.available():
            return None
        return screen_reader.read_screen_ocr_sync(max_chars)
    except Exception as e:  # noqa: BLE001
        log.warning("OCR zaxirasi ishlamadi: %s", e)
        return None


# ---------------------------------------------------------------------------
# AX yordamchilari (sinxron, faqat worker thread'da chaqiriladi)
# ---------------------------------------------------------------------------
def available() -> bool:
    return _AS is not None and _NSWorkspace is not None


def is_trusted() -> bool | None:
    """Accessibility ruxsati (AXIsProcessTrusted). pyobjc bo'lmasa None."""
    if not available():
        return None
    try:
        return bool(_AS.AXIsProcessTrusted())
    except Exception:  # noqa: BLE001
        return None


def _precheck() -> dict[str, Any] | None:
    """Umumiy dastlabki tekshiruv: pyobjc va Accessibility. Muammo bo'lsa natija lug'ati."""
    if not available():
        return _result(False, f"{PYOBJC_HINT} ({_IMPORT_ERROR})")
    if is_trusted() is False:
        return _result(False, ACCESSIBILITY_HINT)
    return None


def _attr(element: Any, name: str) -> Any:
    try:
        err, value = _AS.AXUIElementCopyAttributeValue(element, name, None)
        return value if err == 0 else None
    except Exception:  # noqa: BLE001
        return None


def _label(element: Any) -> str:
    attrs = {name: _attr(element, name) for name in LABEL_ATTRS}
    return pick_label(attrs)


def _unwrap(value: Any, kind: int) -> Any:
    if value is None:
        return None
    try:
        ok, unwrapped = _AS.AXValueGetValue(value, kind, None)
        return unwrapped if ok else None
    except Exception:  # noqa: BLE001
        return None


def _geometry(element: Any) -> tuple[tuple[int, int], tuple[int, int]] | None:
    rect = _unwrap(_attr(element, "AXFrame"), _AS.kAXValueCGRectType)
    if rect is not None:
        origin, size = rect.origin, rect.size
    else:
        origin = _unwrap(_attr(element, "AXPosition"), _AS.kAXValueCGPointType)
        size = _unwrap(_attr(element, "AXSize"), _AS.kAXValueCGSizeType)
        if origin is None or size is None:
            return None
    if size.width <= 0 or size.height <= 0:
        return None
    centre = (round(origin.x + size.width / 2), round(origin.y + size.height / 2))
    return centre, (round(size.width), round(size.height))


def enable_full_tree(pid: int, app_name: str = "") -> None:
    """Chromium/Electron ilovalaridan to'liq veb-daraxtni so'raydi (jarayon uchun bir marta).

    Qt ilovalar (Telegram, WPS ...) uchun daraxt to'lishini `QT_SETTLE_S` kutadi.
    """
    if pid in _ENABLED_PIDS or not available():
        return
    root = _AS.AXUIElementCreateApplication(pid)
    for attribute in ("AXManualAccessibility", "AXEnhancedUserInterface"):
        try:
            _AS.AXUIElementSetAttributeValue(root, attribute, True)
        except Exception as e:  # noqa: BLE001 - tabiiy ilovalarda qo'llanmaydi, zararsiz
            log.debug("%s o'rnatilmadi (pid %s): %s", attribute, pid, e)
    _ENABLED_PIDS.add(pid)
    if is_qt_app(app_name):
        time.sleep(QT_SETTLE_S)


def front_app() -> tuple[str, int] | None:
    try:
        app = _NSWorkspace.sharedWorkspace().frontmostApplication()
    except Exception:  # noqa: BLE001
        return None
    if app is None:
        return None
    return str(app.localizedName() or ""), int(app.processIdentifier())


def _app_root(pid: int) -> Any:
    root = _AS.AXUIElementCreateApplication(pid)
    try:
        _AS.AXUIElementSetMessagingTimeout(root, AX_TIMEOUT_S)
    except Exception as e:  # noqa: BLE001
        log.debug("AX timeout o'rnatilmadi: %s", e)
    return root


def _front_window(root: Any) -> Any:
    window = _attr(root, "AXFocusedWindow") or _attr(root, "AXMainWindow")
    if window is None:
        windows = _attr(root, "AXWindows")
        window = windows[0] if windows else root
    return window


def _walk(start: Any, visit: Any, limit_visited: int = MAX_VISITED) -> int:
    """Chuqurlik bo'yicha yurish. `visit(element, role, depth)` False qaytarsa to'xtaydi."""
    visited = 0
    stack: list[tuple[Any, int]] = [(start, 0)]
    while stack:
        element, depth = stack.pop()
        if depth > MAX_DEPTH or visited >= limit_visited:
            continue
        visited += 1
        role = _attr(element, "AXRole") or ""
        if visit(element, role, depth) is False:
            break
        children = _attr(element, "AXChildren") or []
        # stack — teskari tartibda qo'shamiz, shunda ekrandagi tartib saqlanadi
        for child in reversed(list(children)):
            stack.append((child, depth + 1))
    return visited


def collect_elements(limit: int = 120) -> tuple[str, list[Element]]:
    """Oldingi oynadagi bosiladigan elementlar (yorliqli), ekran koordinatalari bilan."""
    info = front_app()
    if info is None:
        return "", []
    app_name, pid = info
    enable_full_tree(pid, app_name)
    root = _app_root(pid)
    window = _front_window(root)

    found: list[Element] = []
    seen: set[tuple[str, tuple[int, int]]] = set()

    def visit(element: Any, role: str, depth: int) -> bool | None:
        if len(found) >= limit:
            return False
        if role in ACTIONABLE:
            geometry = _geometry(element)
            if geometry is None:
                return None
            centre, size = geometry
            label = _label(element)
            key = (label, centre)
            if label and key not in seen:
                seen.add(key)
                found.append(Element(len(found) + 1, role, label, centre, size, ref=element))
        return None

    _walk(window, visit)
    _LAST_LISTING.update(pid=pid, items=found, source="ax")
    return app_name, found


def collect_elements_with_ocr(limit: int = 120) -> tuple[str, list[Element], str]:
    """AX elementlar + (kam bo'lsa yoki Qt ilova) OCR satrlari. Qaytaradi (app, elementlar, source)."""
    app_name, found = collect_elements(limit)
    if not needs_elements_fallback(app_name, len(found)):
        return app_name, found, "ax"
    ocr = _ocr_read()
    if not ocr or not ocr.get("lines"):
        return app_name, found, "ax"
    extra = ocr_elements(ocr["lines"], start=len(found) + 1)
    merged = found + extra
    source = "ax+ocr" if found else "ocr"
    _LAST_LISTING.update(items=merged, source=source)
    return app_name or ocr.get("app", ""), merged, source


def collect_text(limit_chars: int = 6000) -> tuple[str, str]:
    info = front_app()
    if info is None:
        return "", ""
    app_name, pid = info
    enable_full_tree(pid, app_name)
    root = _app_root(pid)
    window = _front_window(root)
    pieces: list[str] = []
    total = 0

    def visit(element: Any, role: str, depth: int) -> bool | None:
        nonlocal total
        if total > limit_chars:
            return False
        if role in READABLE_ROLES:
            value = _attr(element, "AXValue")
            if not isinstance(value, str) or not value.strip():
                value = _attr(element, "AXTitle")
            if isinstance(value, str):
                text = " ".join(value.split())
                if text and (not pieces or pieces[-1] != text):
                    pieces.append(text)
                    total += len(text) + 1
        return None

    _walk(window, visit)
    return app_name, "\n".join(pieces)[:limit_chars]


def _perform(element: Any, action: str) -> bool:
    try:
        return _AS.AXUIElementPerformAction(element, action) == 0
    except Exception:  # noqa: BLE001
        return False


def _actions(element: Any) -> list[str]:
    try:
        err, names = _AS.AXUIElementCopyActionNames(element, None)
        return [str(n) for n in (names or [])] if err == 0 else []
    except Exception:  # noqa: BLE001
        return []


def _screen_bounds() -> list[tuple[float, float, float, float]]:
    """Barcha displeylarning (x, y, w, h) to'rtliklari (Quartz global koordinatalari)."""
    bounds: list[tuple[float, float, float, float]] = []
    if _QZ is None:
        return bounds
    try:
        _err, ids, _count = _QZ.CGGetActiveDisplayList(16, None, None)
        for did in ids or []:
            r = _QZ.CGDisplayBounds(did)
            bounds.append((r.origin.x, r.origin.y, r.size.width, r.size.height))
    except Exception as e:  # noqa: BLE001
        log.debug("Displey chegaralari olinmadi: %s", e)
    return bounds


def _on_screen(x: float, y: float) -> bool:
    bounds = _screen_bounds()
    if not bounds:
        return True
    return any(bx <= x <= bx + bw and by <= y <= by + bh for bx, by, bw, bh in bounds)


def quartz_click(x: float, y: float, clicks: int = 1) -> tuple[bool, str]:
    """Quartz orqali haqiqiy sichqoncha bosishi (global ekran koordinatalari, yuqori-chap kelib chiqish)."""
    if _QZ is None:
        return False, PYOBJC_HINT
    try:
        point = (float(x), float(y))
        move = _QZ.CGEventCreateMouseEvent(None, _QZ.kCGEventMouseMoved, point, _QZ.kCGMouseButtonLeft)
        _QZ.CGEventPost(_QZ.kCGHIDEventTap, move)
        time.sleep(0.05)
        for i in range(1, clicks + 1):
            down = _QZ.CGEventCreateMouseEvent(None, _QZ.kCGEventLeftMouseDown, point, _QZ.kCGMouseButtonLeft)
            up = _QZ.CGEventCreateMouseEvent(None, _QZ.kCGEventLeftMouseUp, point, _QZ.kCGMouseButtonLeft)
            _QZ.CGEventSetIntegerValueField(down, _QZ.kCGMouseEventClickState, i)
            _QZ.CGEventSetIntegerValueField(up, _QZ.kCGMouseEventClickState, i)
            _QZ.CGEventPost(_QZ.kCGHIDEventTap, down)
            time.sleep(0.03)
            _QZ.CGEventPost(_QZ.kCGHIDEventTap, up)
            time.sleep(0.05)
        return True, f"bosildi ({round(x)}, {round(y)})"
    except Exception as e:  # noqa: BLE001
        return False, f"Quartz klik xatosi: {type(e).__name__}: {e}"


def activate_element(el: Element) -> tuple[bool, str]:
    """Avval AXPress; bo'lmasa (yoki qo'llanmasa) markazga Quartz klik."""
    ref = el.ref
    if ref is not None and "AXPress" in _actions(ref) and _perform(ref, "AXPress"):
        return True, f"'{el.label}' AXPress bilan bosildi"
    x, y = el.at
    if ref is not None and not _on_screen(x, y):
        _perform(ref, "AXScrollToVisible")
        time.sleep(0.15)
        geometry = _geometry(ref)
        if geometry is not None:
            (x, y), _ = geometry
    ok, msg = quartz_click(x, y)
    if ok:
        return True, f"'{el.label}' sichqoncha bilan bosildi ({x}, {y})"
    return False, msg


def menu_tree(max_items: int = 40) -> dict[str, list[str]]:
    info = front_app()
    if info is None:
        return {}
    _, pid = info
    bar = _attr(_app_root(pid), "AXMenuBar")
    if bar is None:
        return {}
    tree: dict[str, list[str]] = {}
    for top in _attr(bar, "AXChildren") or []:
        title = _clean_text(_attr(top, "AXTitle"))
        if not title or title == "Apple":
            continue
        items: list[str] = []
        for menu in _attr(top, "AXChildren") or []:
            for item in _attr(menu, "AXChildren") or []:
                name = _clean_text(_attr(item, "AXTitle"))
                if name:
                    items.append(name)
                if len(items) >= max_items:
                    break
        tree[title] = items
    return tree


def run_menu(path: list[str]) -> tuple[bool, str]:
    """Menyu yo'li bo'yicha element topib AXPress qiladi, masalan ["File", "Save"]."""
    if not path:
        return False, "Menyu yo'li bo'sh"
    info = front_app()
    if info is None:
        return False, "Oldingi ilova topilmadi"
    app_name, pid = info
    bar = _attr(_app_root(pid), "AXMenuBar")
    if bar is None:
        return False, f"{app_name} menyu panelini ochib bermaydi"

    node = bar
    for part in path:
        children = list(_attr(node, "AXChildren") or [])
        pool = list(children)
        for child in children:
            if (_attr(child, "AXRole") or "") == "AXMenu":
                pool.extend(_attr(child, "AXChildren") or [])
        titled = [(c, _clean_text(_attr(c, "AXTitle"))) for c in pool]
        titled = [(c, t) for c, t in titled if t]
        best: tuple[float, Any] | None = None
        for candidate, title in titled:
            score = _match_label(part, title)
            if score and (best is None or score > best[0]):
                best = (score, candidate)
        if best is None:
            names = [t for _, t in titled][:25]
            return False, f"'{part}' menyu bandi topilmadi ({app_name}). Mavjud: {names}"
        node = best[1]

    if _perform(node, "AXPress"):
        return True, f"{' > '.join(path)} bajarildi ({app_name})"
    return False, f"{' > '.join(path)} topildi, lekin bosib bo'lmadi ({app_name})"


def focused_element() -> dict[str, Any] | None:
    info = front_app()
    if info is None:
        return None
    app_name, pid = info
    root = _app_root(pid)
    el = _attr(root, "AXFocusedUIElement")
    if el is None:
        return {"app": app_name, "role": None, "label": ""}
    role = str(_attr(el, "AXRole") or "")
    value = _attr(el, "AXValue")
    geometry = _geometry(el)
    out: dict[str, Any] = {
        "app": app_name,
        "role": role.removeprefix("AX"),
        "label": _label(el),
        "editable": role in TEXT_ROLES,
    }
    if isinstance(value, str):
        out["value"] = _clean_text(value, 400)
    if geometry is not None:
        out["at"], out["size"] = list(geometry[0]), list(geometry[1])
    window = _front_window(root)
    title = _clean_text(_attr(window, "AXTitle"))
    if title:
        out["window"] = title
    return out


def set_field_value(label: str, text: str) -> tuple[bool, str]:
    app_name, found = collect_elements(limit=400)
    fields = [e for e in found if e.role in TEXT_ROLES]
    ranked = rank_matches(label, fields)
    if not ranked:
        names = [e.label for e in fields][:20]
        return False, f"'{label}' nomli matn maydoni topilmadi ({app_name}). Mavjud: {names}"
    el = ranked[0][1]
    try:
        err = _AS.AXUIElementSetAttributeValue(el.ref, "AXValue", text)
    except Exception as e:  # noqa: BLE001
        return False, f"AXValue o'rnatilmadi: {type(e).__name__}: {e}"
    if err == 0:
        return True, f"'{el.label}' maydoniga matn yozildi ({len(text)} belgi)"
    try:
        _AS.AXUIElementSetAttributeValue(el.ref, "AXFocused", True)
    except Exception as e:  # noqa: BLE001
        log.debug("AXFocused o'rnatilmadi: %s", e)
    return False, (
        f"'{el.label}' maydoni AXValue orqali yozishni qo'llamaydi (kod {err}); "
        "maydon fokuslandi — type_text bilan yozib ko'ring."
    )


# ---------------------------------------------------------------------------
# Handlerlar (async)
# ---------------------------------------------------------------------------
async def list_ui_elements(args: dict[str, Any]) -> dict[str, Any]:
    pre = _precheck()
    if pre:
        return pre
    limit = int(args.get("max_items") or 120)
    limit = max(1, min(limit, 400))
    needle = str(args.get("filter") or "").strip()
    app, found, source = await asyncio.to_thread(collect_elements_with_ocr, limit)
    items = [e.as_dict() for e in found]
    if needle:
        items = [i for i in items if _match_label(needle, i["label"]) > 0]
    if not items:
        note = (
            f"{app or 'Ilova'} birorta bosiladigan element ko'rsatmadi"
            + (f" ('{needle}' filtri bilan)" if needle else "")
            + ". Chrome/Electron bo'lsa bir necha soniyadan keyin qayta urinib ko'ring; "
            "yoki look_at_screen bilan ekranni ko'ring."
        )
        return _result(True, {"app": app, "count": 0, "elements": []}, source=source, note=note)
    note = "Pozitsiyalar tizimdan olingan — aniq. click_ui_element(label yoki index=n) bilan bosing."
    if source != "ax":
        note = (
            f"{OCR_NOTE}: role='text' elementlar ekrandagi matn satrlari (OCR), "
            "click_ui_element(label yoki index=n) ularning markazini bosadi."
        )
    return _result(True, {"app": app, "count": len(items), "elements": items}, source=source, note=note)


async def click_ui_element(args: dict[str, Any]) -> dict[str, Any]:
    label = str(args.get("label") or "").strip()
    index = args.get("index")
    x, y = args.get("x"), args.get("y")

    if not label and index is None:
        if x is None or y is None:
            return _result(False, "label, index yoki x va y ko'rsatilishi kerak")
        if _QZ is None:
            return _result(False, f"{PYOBJC_HINT} ({_IMPORT_ERROR})")
        ok, msg = await asyncio.to_thread(quartz_click, float(x), float(y))
        return _result(
            ok, msg, note="Koordinata bo'yicha bosildi; natijani read_screen_text bilan tekshiring."
        )

    pre = _precheck()
    if pre:
        return pre

    def _work() -> dict[str, Any]:
        info = front_app()
        pid = info[1] if info else None
        cached: list[Element] = _LAST_LISTING["items"] if _LAST_LISTING["pid"] == pid else []

        if index is not None:
            n = int(index)
            target = next((e for e in cached if e.n == n), None)
            if target is None or (target.ref is not None and _geometry(target.ref) is None):
                _app, fresh, _src = collect_elements_with_ocr(limit=max(120, n))
                target = next((e for e in fresh if e.n == n), None)
            if target is None:
                return _result(False, f"index={n} element topilmadi; avval list_ui_elements chaqiring")
            if label and _match_label(label, target.label) == 0:
                log.info("index=%s yorlig'i '%s' so'ralgan '%s' ga mos emas", n, target.label, label)
            ok, msg = activate_element(target)
            return _result(
                ok, msg, at=list(target.at), next_step="Natijani read_screen_text bilan tekshiring."
            )

        app, found, _src = collect_elements_with_ocr(limit=400)
        ranked = rank_matches(label, found)
        if not ranked and _src == "ax":
            # AX'da topilmadi — OCR satrlari orasidan ham qidiramiz
            ocr = _ocr_read()
            if ocr and ocr.get("lines"):
                found = found + ocr_elements(ocr["lines"], start=len(found) + 1)
                _LAST_LISTING.update(items=found, source="ax+ocr")
                ranked = rank_matches(label, found)
        if not ranked:
            visible = [e.label for e in found][:25]
            return _result(
                False,
                f"'{label}' nomli element topilmadi ({app or 'oldingi oyna'}). Ko'rinadiganlar: {visible}",
            )
        best_score = ranked[0][0]
        ties = [e for s, e in ranked if s == best_score]
        if len(ties) > 1:
            matches = [e.as_dict() for e in ties[:8]]
            return _result(
                False,
                {"needs_choice": True, "matches": matches},
                needs_choice=True,
                matches=matches,
                note=(
                    f"{len(ties)} ta element '{label}' ga mos keladi. Kerakli raqam (n) bilan "
                    "click_ui_element(index=n) chaqiring. Kattarog'i odatda asosiy amal."
                ),
            )
        target = ties[0]
        ok, msg = activate_element(target)
        return _result(ok, msg, at=list(target.at), next_step="Natijani read_screen_text bilan tekshiring.")

    return await asyncio.to_thread(_work)


async def read_screen_text(args: dict[str, Any]) -> dict[str, Any]:
    pre = _precheck()
    if pre:
        return pre
    limit = int(args.get("max_chars") or 6000)
    limit = max(200, min(limit, 20000))
    app, text = await asyncio.to_thread(collect_text, limit)
    next_step = "Foydalanuvchiga so'ragan narsasini 1-2 jumla bilan ayting; butun sahifani o'qimang."
    if needs_text_fallback(app, text):
        ocr = await asyncio.to_thread(_ocr_read, limit)
        if ocr and ocr.get("text"):
            return _result(
                True,
                {
                    "app": ocr.get("app") or app,
                    "chars": len(ocr["text"]),
                    "lines": ocr["count"],
                    "text": ocr["text"],
                },
                source="ocr",
                note=OCR_NOTE,
                next_step=next_step,
            )
    if not text:
        return _result(
            True,
            {"app": app, "text": ""},
            source="ax",
            note="O'qiladigan matn yo'q (ilova AX matn bermaydi, OCR ham topmadi). look_at_screen bilan ko'ring.",
        )
    return _result(True, {"app": app, "chars": len(text), "text": text}, source="ax", next_step=next_step)


async def list_menus(args: dict[str, Any]) -> dict[str, Any]:
    pre = _precheck()
    if pre:
        return pre
    tree = await asyncio.to_thread(menu_tree)
    if not tree:
        return _result(False, "Oldingi ilova menyu panelini ko'rsatmadi")
    return _result(True, {"menus": tree})


async def menu_command(args: dict[str, Any]) -> dict[str, Any]:
    pre = _precheck()
    if pre:
        return pre
    raw = args.get("path")
    if isinstance(raw, str):
        parts = [p.strip() for p in re.split(r"\s*(?:>|→|/|,)\s*", raw) if p.strip()]
    else:
        parts = [str(p).strip() for p in (raw or []) if str(p).strip()]
    if not parts:
        return _result(False, "path bo'sh — masalan ['File', 'Save']")
    ok, msg = await asyncio.to_thread(run_menu, parts)
    return _result(ok, msg)


async def get_focused_element(args: dict[str, Any]) -> dict[str, Any]:
    pre = _precheck()
    if pre:
        return pre
    info = await asyncio.to_thread(focused_element)
    if info is None:
        return _result(False, "Oldingi ilova topilmadi")
    return _result(True, info)


async def set_text_field(args: dict[str, Any]) -> dict[str, Any]:
    pre = _precheck()
    if pre:
        return pre
    label = str(args.get("label") or "").strip()
    text = str(args.get("text") if args.get("text") is not None else "")
    if not label:
        return _result(False, "label kerak")
    ok, msg = await asyncio.to_thread(set_field_value, label, text)
    return _result(ok, msg)


# ---------------------------------------------------------------------------
# Deklaratsiyalar
# ---------------------------------------------------------------------------
_LANG = " The user may speak Uzbek, Russian or English."


def _decl(name: str, description: str, props: dict | None = None, required: list[str] | None = None) -> dict:
    d: dict[str, Any] = {"name": name, "description": description + _LANG}
    if props:
        d["parameters"] = {"type": "OBJECT", "properties": props, "required": required or []}
    return d


def _s(desc: str) -> dict:
    return {"type": "STRING", "description": desc}


def _i(desc: str) -> dict:
    return {"type": "INTEGER", "description": desc}


def _n(desc: str) -> dict:
    return {"type": "NUMBER", "description": desc}


TOOL_DECLARATIONS: list[dict] = [
    _decl(
        "list_ui_elements",
        "List the buttons, links, fields, tabs and rows of the frontmost window with exact screen positions "
        "read from macOS Accessibility. Use this FIRST when you need to press something in an app; it is exact, "
        "unlike guessing from a screenshot.",
        {
            "filter": _s("Optional text to narrow the list, e.g. 'save', 'yangi'."),
            "max_items": _i("Maximum elements to return (default 120)."),
        },
    ),
    _decl(
        "click_ui_element",
        "Click a control in the frontmost window by its name (as listed by list_ui_elements), by its number "
        "(index=n), or at exact screen coordinates. Prefer label/index over coordinates. If several controls "
        "match, the result lists them and you must call again with index.",
        {
            "label": _s("The control's visible name, e.g. 'Save', 'Sign in', 'Yangi'."),
            "index": _i("Number n from list_ui_elements / the matches list."),
            "x": _n("Screen x (only when no named control exists)."),
            "y": _n("Screen y (only when no named control exists)."),
        },
    ),
    _decl(
        "read_screen_text",
        "Read the real text of the frontmost window (web page, document, chat, form) from macOS Accessibility, "
        "falling back to on-device OCR of a screenshot when the app exposes no text (Telegram, Qt/Electron). "
        "Use it to answer 'what does this say?', find a price/name/message, or to check what a click did.",
        {"max_chars": _i("How many characters to read (default 6000).")},
    ),
    _decl(
        "list_menus",
        "Read the menu bar of the frontmost app (File, Edit, View ...) with their items.",
    ),
    _decl(
        "menu_command",
        "Run a menu command of the frontmost app by path, e.g. ['File','Save'] or ['Format','Bold']. "
        "The most reliable way to make an app do something.",
        {
            "path": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "description": "Menu titles from top level to the item, e.g. ['File', 'New Document'].",
            }
        },
        ["path"],
    ),
    _decl(
        "get_focused_element",
        "Describe the currently focused control (app, window, role, label, value) — e.g. to check whether "
        "a text field is active before typing or dictating.",
    ),
    _decl(
        "set_text_field",
        "Put text directly into a named text field of the frontmost window (replaces its content) via "
        "Accessibility, without keystrokes.",
        {"label": _s("Field name/placeholder, e.g. 'Search', 'Email'."), "text": _s("Text to set.")},
        ["label", "text"],
    ),
]

HANDLERS: dict[str, Any] = {
    "list_ui_elements": list_ui_elements,
    "click_ui_element": click_ui_element,
    "read_screen_text": read_screen_text,
    "list_menus": list_menus,
    "menu_command": menu_command,
    "get_focused_element": get_focused_element,
    "set_text_field": set_text_field,
}

__all__ = [
    "ACCESSIBILITY_HINT",
    "HANDLERS",
    "PYOBJC_HINT",
    "TOOL_DECLARATIONS",
    "Element",
    "_match_label",
    "available",
    "collect_elements_with_ocr",
    "enable_full_tree",
    "is_qt_app",
    "is_trusted",
    "needs_elements_fallback",
    "needs_text_fallback",
    "ocr_elements",
    "pick_label",
    "rank_matches",
]
