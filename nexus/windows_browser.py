"""Windows'da brauzer boshqaruvi: UI Automation + klaviatura (Chrome, Edge, Firefox).

macOS'da brauzer AppleScript orqali sahifa ichida JS bajaradi. Windows'da bunday kanal yo'q
(Chrome 136+ asosiy profilda DevTools portini ham ochmaydi), shuning uchun:

- tablar, sarlavha, manzil, sahifa matni, havola/tugmalar — UIA daraxtidan;
- yopish/yangilash/aylantirish — klaviatura (Ctrl+W, F5, PageDown...);
- YouTube — pleyerning o'z klavishlari (k, j/l, m, f, c, Shift+N...).

Registry `tabs/dom/youtube/search/search_input` atributlarining hammasiga shu bitta obyektni
beradi — metod nomlari va imzolari macOS sinflari bilan bir xil. CSS selektor bo'yicha bosish
(`click_element`) Windows'da yo'q va Gemini'ga e'lon qilinmaydi.
"""

from __future__ import annotations

import asyncio
import ctypes
import logging
import re
import time
import webbrowser
from dataclasses import dataclass
from typing import Any

from nexus.browser_actions import normalize_url

log = logging.getLogger("nexus.windows_browser")

Result = tuple[bool, str]

# Brauzer kaliti → jarayon nomlari (birinchisi afzal)
BROWSER_PROCESSES: dict[str, tuple[str, ...]] = {
    "chrome": ("chrome",),
    "edge": ("msedge",),
    "firefox": ("firefox",),
}
ALL_BROWSER_PROCESSES = frozenset(p for procs in BROWSER_PROCESSES.values() for p in procs)
# Edge sarlavhasida "Microsoft" dan keyin nol kenglikdagi bo'shliq (U+200B) bor
TITLE_SUFFIXES = (" - Google Chrome", " - Microsoft\u200b Edge", " - Microsoft Edge", " — Mozilla Firefox", " - Mozilla Firefox")
ADDRESS_BAR_NAMES = ("address and search bar", "manzil", "адресная строка", "search with", "enter address")
SEARCH_FIELD_HINTS = ("search", "qidir", "поиск", "find", "izla", "query")
NEXT_PAGE_NAMES = ("next", "keyingi", "следующая", "далее", "next page")
PREV_PAGE_NAMES = ("previous", "oldingi", "предыдущая", "назад", "previous page")
# Qidiruv natijasi bo'lmagan havolalar (Google/Bing navigatsiyasi)
RESULT_NOISE = re.compile(
    r"^(images|videos|news|maps|shopping|books|more|tools|settings|sign in|privacy|terms|help|feedback|"
    r"rasmlar|videolar|yangiliklar|xaritalar|ko'proq|kirish|next|previous|keyingi|oldingi|\d+)$",
    re.IGNORECASE,
)
SCROLL_PAGE_PX = 600
YOUTUBE_SEEK_KEY_S = 10  # j / l
YOUTUBE_ARROW_S = 5  # chap / o'ng o'q
YOUTUBE_VOLUME_STEP = 5  # yuqori / pastki o'q
YOUTUBE_SPEED_STEP = 0.25


@dataclass
class BrowserWindow:
    hwnd: int
    process: str
    title: str

    @property
    def page_title(self) -> str:
        t = self.title
        for suffix in TITLE_SUFFIXES:
            if t.endswith(suffix):
                t = t[: -len(suffix)]
                break
        # Edge/Chrome profil nomi: "Sahifa - Profile 1"
        return re.sub(r" - Profile \d+$", "", t)

    @property
    def label(self) -> str:
        return {"chrome": "Chrome", "msedge": "Edge", "firefox": "Firefox"}.get(self.process, self.process)


def browser_key(browser: str | None) -> str | None:
    """'chrome' / 'edge' / 'firefox' yoki None (istalgan). macOS'dagi 'safari' — istalgan brauzer."""
    b = (browser or "").strip().lower()
    if b in ("", "default", "safari"):
        return None
    if "edge" in b:
        return "edge"
    if "firefox" in b or b == "ff":
        return "firefox"
    if "chrome" in b or b == "gc":
        return "chrome"
    return None


def pick_window(windows: list[BrowserWindow], browser: str | None) -> BrowserWindow | None:
    """Z-tartib bo'yicha birinchi mos brauzer oynasi (so'ralgani bo'lmasa — istalgan brauzer)."""
    key = browser_key(browser)
    if key is not None:
        procs = BROWSER_PROCESSES[key]
        for w in windows:
            if w.process in procs:
                return w
    return windows[0] if windows else None


def seek_presses(seconds: float) -> list[tuple[str, int]]:
    """Nisbiy siljish → klavishlar: 10 s lik l/j, qoldig'i 5 s lik o'qlar."""
    secs = round(seconds)
    if secs == 0:
        return []
    forward = secs > 0
    tens, rest = divmod(abs(secs), YOUTUBE_SEEK_KEY_S)
    fives = round(rest / YOUTUBE_ARROW_S)
    out: list[tuple[str, int]] = []
    if tens:
        out.append(("l" if forward else "j", tens))
    if fives:
        out.append(("right" if forward else "left", fives))
    return out


def speed_presses(rate: float) -> list[tuple[str, int]]:
    """Tezlik: avval minimal (0.25) gacha tushirib, keyin kerakli qadamlar."""
    rate = max(0.25, min(2.0, float(rate)))
    ups = round((rate - 0.25) / YOUTUBE_SPEED_STEP)
    out = [("shift+,", 8)]
    if ups:
        out.append(("shift+.", ups))
    return out


def looks_like_result(name: str) -> bool:
    n = name.strip()
    return len(n) >= 12 and not RESULT_NOISE.match(n) and not n.lower().startswith(("http://", "https://"))


# ---------------------------------------------------------------------------
# Windows API (faqat Windows'da chaqiriladi)
# ---------------------------------------------------------------------------
DOC_TRIES = 5
DOC_RETRY_S = 0.6


def document_tree(root: Any, tries: int = DOC_TRIES) -> list[Any]:
    """Sahifa (DocumentControl) elementlari. Chromium veb-kontent daraxtini UIA mijozi birinchi
    so'raganda quradi — birinchi o'tishda hujjat bo'sh bo'ladi, shuning uchun qisqa qayta urinish."""
    from nexus.windows_screen import _walk

    docs: list[Any] = []
    for attempt in range(tries):
        docs = [c for c in _walk(root, 600) if c.ControlTypeName == "DocumentControl"]
        if docs:
            items = _walk(docs[0], 3000)
            if len(items) > 1:
                return items
        if attempt < tries - 1:
            time.sleep(DOC_RETRY_S)
    return _walk(docs[0] if docs else root, 3000)

def list_browser_windows() -> list[BrowserWindow]:
    """Ko'rinadigan brauzer oynalari, Z-tartibda (eng ustidagisi birinchi)."""
    import psutil

    from nexus.windows_screen import _window_pid, _window_title

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    found: list[BrowserWindow] = []
    names: dict[int, str] = {}

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def _cb(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd) or user32.GetWindow(hwnd, 4):  # GW_OWNER — popup emas
            return True
        title = _window_title(hwnd)
        if not title.strip():
            return True
        pid = _window_pid(hwnd)
        if pid not in names:
            try:
                names[pid] = psutil.Process(pid).name().lower().removesuffix(".exe")
            except psutil.Error:
                names[pid] = ""
        if names[pid] in ALL_BROWSER_PROCESSES:
            found.append(BrowserWindow(int(hwnd), names[pid], title))
        return True

    user32.EnumWindows(_cb, 0)
    return found


class WindowsBrowser:
    """Brauzer amallari — macOS'dagi BrowserController/DOM/YouTube/Search sinflari bilan bir xil API."""

    # -- oyna --------------------------------------------------------------
    async def _window(self, browser: str) -> BrowserWindow | None:
        windows = await asyncio.to_thread(list_browser_windows)
        return pick_window(windows, browser)

    async def _focused(self, browser: str) -> tuple[BrowserWindow | None, str]:
        win = await self._window(browser)
        if win is None:
            return None, "Ochiq brauzer oynasi topilmadi — avval browser_open_url bilan sahifa oching"
        from nexus.windows_screen import _activate

        await asyncio.to_thread(_activate, win.hwnd)
        await asyncio.sleep(0.15)
        return win, ""

    async def _keys(self, browser: str, *combos: tuple[str, int]) -> tuple[BrowserWindow | None, str]:
        from nexus import windows_input

        win, err = await self._focused(browser)
        if win is None:
            return None, err
        for keys, times in combos:
            for _ in range(times):
                await asyncio.to_thread(windows_input.press_combo, keys)
                await asyncio.sleep(0.03)
        return win, ""

    @staticmethod
    def _uia_run(hwnd: int, fn: Any) -> Any:
        """`fn(auto, root)` ni UIA ishga tushirilgan thread'da bajaradi."""
        from nexus.windows_screen import _ensure_dpi_aware, _uia

        def run() -> Any:
            _ensure_dpi_aware()
            auto = _uia()
            with auto.UIAutomationInitializerInThread():
                return fn(auto, auto.ControlFromHandle(hwnd))

        return asyncio.to_thread(run)

    # -- tablar (BrowserController) ---------------------------------------
    async def open_url(self, browser: str, url: str) -> Result:
        target = normalize_url(url)
        ok = await asyncio.to_thread(webbrowser.open, target, 2)
        return (True, f"Brauzerda ochildi: {target}") if ok else (False, f"Sahifani ochib bo'lmadi: {target}")

    async def close_current_tab(self, browser: str) -> Result:
        win, err = await self._keys(browser, ("ctrl+w", 1))
        return (True, f"{win.label}: tab yopildi ({win.page_title})") if win else (False, err)

    async def reload(self, browser: str) -> Result:
        win, err = await self._keys(browser, ("f5", 1))
        return (True, f"{win.label}: sahifa yangilandi") if win else (False, err)

    async def current_page(self, browser: str) -> Result:
        win = await self._window(browser)
        if win is None:
            return False, "Ochiq brauzer oynasi topilmadi"
        url = await self._address(win)
        return True, f"{win.label}: {win.page_title}" + (f" — {url}" if url else "")

    async def current_url(self, browser: str) -> Result:
        win = await self._window(browser)
        if win is None:
            return False, "Ochiq brauzer oynasi topilmadi"
        url = await self._address(win)
        return (True, url) if url else (False, "Manzilni o'qib bo'lmadi")

    async def _address(self, win: BrowserWindow) -> str:
        from nexus.windows_screen import _value, _walk

        def work(auto: Any, root: Any) -> str:
            for c in _walk(root, 600):
                if c.ControlTypeName == "EditControl" and any(n in (c.Name or "").lower() for n in ADDRESS_BAR_NAMES):
                    return _value(c)
            return ""

        try:
            return await self._uia_run(win.hwnd, work)
        except Exception as e:  # noqa: BLE001
            log.debug("Manzil o'qilmadi: %s", e)
            return ""

    async def _tabs(self, win: BrowserWindow) -> list[Any]:
        from nexus.windows_screen import _walk

        def work(auto: Any, root: Any) -> list[tuple[str, bool]]:
            tabs = []
            for c in _walk(root, 1500):
                if c.ControlTypeName == "TabItemControl" and c.Name:
                    try:
                        sel = c.GetSelectionItemPattern()
                        selected = bool(sel.IsSelected) if sel else False
                    except Exception:  # noqa: BLE001
                        selected = False
                    tabs.append((c.Name, selected))
            return tabs

        return await self._uia_run(win.hwnd, work)

    async def list_tabs(self, browser: str, limit: int = 30) -> Result:
        win = await self._window(browser)
        if win is None:
            return False, "Ochiq brauzer oynasi topilmadi"
        try:
            tabs = await self._tabs(win)
        except Exception as e:  # noqa: BLE001
            return False, f"Tablarni o'qib bo'lmadi: {e}"
        if not tabs:
            return True, f"{win.label}: {win.page_title} (tablar ro'yxati o'qilmadi)"
        lines = [f"{i}. {name}{' (faol)' if sel else ''}" for i, (name, sel) in enumerate(tabs[:limit], 1)]
        return True, f"{win.label}, {len(tabs)} ta tab:\n" + "\n".join(lines)

    async def switch_to_tab(self, browser: str, keyword: str) -> Result:
        win = await self._window(browser)
        if win is None:
            return False, "Ochiq brauzer oynasi topilmadi"
        want = (keyword or "").strip().lower()
        if not want:
            return False, "Tab uchun kalit so'z kerak"
        from nexus.windows_screen import _activate, _walk

        def work(auto: Any, root: Any) -> str | None:
            for c in _walk(root, 1500):
                if c.ControlTypeName == "TabItemControl" and want in (c.Name or "").lower():
                    _activate(win.hwnd)
                    try:
                        c.GetSelectionItemPattern().Select()
                    except Exception:  # noqa: BLE001
                        c.Click(simulateMove=False)
                    return c.Name
            return None

        try:
            name = await self._uia_run(win.hwnd, work)
        except Exception as e:  # noqa: BLE001
            return False, f"Tabga o'tib bo'lmadi: {e}"
        return (True, f"Tabga o'tildi: {name}") if name else (False, f"'{keyword}' bo'yicha tab topilmadi")

    async def set_current_url(self, browser: str, url: str) -> Result:
        from nexus import windows_input

        win, err = await self._keys(browser, ("ctrl+l", 1))
        if win is None:
            return False, err
        await asyncio.to_thread(windows_input.type_unicode, normalize_url(url))
        await asyncio.to_thread(windows_input.press_enter)
        return True, f"{win.label}: {normalize_url(url)} ochildi"

    # -- sahifa (BrowserDOMController) ------------------------------------
    async def scroll_page(self, browser: str, direction: str = "down", pixels: int = 600) -> Result:
        d = (direction or "down").lower()
        pages = max(1, round(int(pixels or SCROLL_PAGE_PX) / SCROLL_PAGE_PX))
        combo = {"down": ("pagedown", pages), "up": ("pageup", pages), "top": ("home", 1), "bottom": ("end", 1)}.get(d)
        if combo is None:
            return False, f"Noma'lum yo'nalish: {direction} (down|up|top|bottom)"
        win, err = await self._keys(browser, combo)
        return (True, f"{win.label}: sahifa aylantirildi ({d})") if win else (False, err)

    async def scroll_to(self, browser: str, position: str | int) -> Result:
        return await self.scroll_page(browser, "top" if str(position) in ("0", "top") else "bottom")

    async def _document_controls(self, win: BrowserWindow) -> Any:
        """Sahifa (DocumentControl) ichidagi elementlar; hujjat topilmasa — butun oyna."""

        def work(auto: Any, root: Any) -> list[Any]:
            return document_tree(root)

        return await self._uia_run(win.hwnd, work)

    async def click_by_text(self, browser: str, text: str, tag: str | None = None) -> Result:
        from nexus.windows_screen import _activate, _press, collect_elements, find_by_label

        win, err = await self._focused(browser)
        if win is None:
            return False, err

        def work(auto: Any, root: Any) -> Result:
            elements = collect_elements(document_tree(root), "", 600)
            matches = find_by_label(elements, text)
            if not matches:
                return False, f"Sahifada '{text}' nomli tugma yoki havola topilmadi"
            _activate(win.hwnd)
            how = _press(matches[0])
            return True, f"Bosildi: {matches[0].name} ({how})"

        try:
            return await self._uia_run(win.hwnd, work)
        except Exception as e:  # noqa: BLE001
            return False, f"Bosib bo'lmadi: {e}"

    async def click_element(self, browser: str, selector: str) -> Result:
        return False, "Windows'da CSS selektor bilan bosish yo'q — browser_click_button(matn) dan foydalaning"

    async def get_page_text_summary(self, browser: str, max_chars: int = 1500) -> Result:
        from nexus.windows_screen import collect_text

        win = await self._window(browser)
        if win is None:
            return False, "Ochiq brauzer oynasi topilmadi"
        try:
            controls = await self._document_controls(win)
        except Exception as e:  # noqa: BLE001
            return False, f"Sahifani o'qib bo'lmadi: {e}"
        text = collect_text(controls, max(200, int(max_chars or 1500)))
        if not text.strip():
            return False, "Sahifa matni o'qilmadi — read_screen_ocr yoki look_at_screen bilan ko'ring"
        return True, f"{win.page_title}\n\n{text}"

    async def get_page_links(self, browser: str, limit: int = 30) -> Result:
        ok, links = await self._result_links(browser)
        if not ok:
            return False, str(links)
        return True, "\n".join(f"{i}. {n}" for i, n in enumerate(links[:limit], 1)) or "Havola topilmadi"

    # -- qidiruv (SearchNavigationController / SearchInputController) -----
    async def _result_links(self, browser: str) -> tuple[bool, Any]:
        win = await self._window(browser)
        if win is None:
            return False, "Ochiq brauzer oynasi topilmadi"
        try:
            controls = await self._document_controls(win)
        except Exception as e:  # noqa: BLE001
            return False, f"Natijalarni o'qib bo'lmadi: {e}"
        names: list[str] = []
        for c in controls:
            if c.ControlTypeName == "HyperlinkControl" and not getattr(c, "IsOffscreen", False):
                name = (c.Name or "").strip()
                if looks_like_result(name) and name not in names:
                    names.append(name)
        return True, names

    async def get_results_text(self, browser: str, limit: int = 10) -> Result:
        ok, links = await self._result_links(browser)
        if not ok:
            return False, str(links)
        if not links:
            return False, "Sahifada qidiruv natijalari topilmadi"
        return True, "Natijalar:\n" + "\n".join(f"{i}. {n}" for i, n in enumerate(links[:limit], 1))

    async def open_result_by_index(self, browser: str, index: int, new_tab: bool = False) -> Result:
        ok, links = await self._result_links(browser)
        if not ok:
            return False, str(links)
        if not 1 <= int(index) <= len(links):
            return False, f"{index}-natija yo'q (jami {len(links)} ta)"
        return await self.click_by_text(browser, links[int(index) - 1])

    async def open_result_by_match(self, browser: str, keyword: str, new_tab: bool = False) -> Result:
        ok, links = await self._result_links(browser)
        if not ok:
            return False, str(links)
        want = (keyword or "").lower()
        hit = next((n for n in links if want in n.lower()), None)
        if hit is None:
            return False, f"'{keyword}' bo'yicha natija topilmadi"
        return await self.click_by_text(browser, hit)

    async def navigate_page(self, browser: str, direction: str = "next") -> Result:
        names = NEXT_PAGE_NAMES if (direction or "next").lower() == "next" else PREV_PAGE_NAMES
        for name in names:
            ok, _out = await self.click_by_text(browser, name)
            if ok:
                return True, f"{'Keyingi' if names is NEXT_PAGE_NAMES else 'Oldingi'} sahifa ochildi"
        return False, "Sahifalash havolasi topilmadi"

    async def type_query_and_search(self, browser: str, query: str, auto_submit: bool = True) -> Result:
        from nexus import windows_input
        from nexus.windows_screen import _activate

        q = (query or "").strip()
        if not q:
            return False, "Qidiruv so'rovi bo'sh"
        win, err = await self._focused(browser)
        if win is None:
            return False, err

        def work(auto: Any, root: Any) -> str | None:
            for c in document_tree(root):
                if c.ControlTypeName not in ("EditControl", "ComboBoxControl") or getattr(c, "IsOffscreen", False):
                    continue
                label = f"{c.Name} {getattr(c, 'HelpText', '')}".lower()
                if any(h in label for h in SEARCH_FIELD_HINTS):
                    _activate(win.hwnd)
                    c.SetFocus()
                    return c.Name or "qidiruv"
            return None

        try:
            field = await self._uia_run(win.hwnd, work)
        except Exception as e:  # noqa: BLE001
            return False, f"Qidiruv maydoni topilmadi: {e}"
        if field is None:
            return False, "Sahifada qidiruv maydoni topilmadi — web_search dan foydalaning"
        await asyncio.to_thread(windows_input.press_combo, "ctrl+a")
        await asyncio.to_thread(windows_input.type_unicode, q)
        if auto_submit:
            await asyncio.to_thread(windows_input.press_enter)
        return True, f"'{q}' qidirildi ({field})"

    async def clear_search_input(self, browser: str) -> Result:
        return await self.type_query_and_search(browser, " ", auto_submit=False)

    # -- YouTube (YouTubeController) --------------------------------------
    async def _youtube(self, browser: str, *combos: tuple[str, int], label: str) -> Result:
        win = await self._window(browser)
        if win is None:
            return False, "Ochiq brauzer oynasi topilmadi"
        if "youtube" not in win.title.lower():
            return False, f"Faol tab YouTube emas ({win.page_title}) — avval YouTube tabiga o'ting"
        win, err = await self._keys(browser, *combos)
        return (True, f"YouTube: {label}") if win else (False, err)

    async def _is_playing(self, browser: str) -> bool | None:
        """Pleyer tugmasining nomi: "Pause (k)" — ijro etilmoqda, "Play (k)" — pauzada."""
        win = await self._window(browser)
        if win is None:
            return None
        from nexus.windows_screen import _walk

        def work(auto: Any, root: Any) -> bool | None:
            for c in _walk(root, 3000):
                name = (c.Name or "").lower()
                if c.ControlTypeName == "ButtonControl" and name.endswith("(k)"):
                    return name.startswith(("pause", "pauza", "пауза"))
            return None

        try:
            return await self._uia_run(win.hwnd, work)
        except Exception:  # noqa: BLE001
            return None

    async def toggle_play(self, browser: str) -> Result:
        return await self._youtube(browser, ("k", 1), label="ijro/pauza almashtirildi")

    async def play(self, browser: str) -> Result:
        if await self._is_playing(browser) is True:
            return True, "YouTube: allaqachon ijro etilmoqda"
        return await self._youtube(browser, ("k", 1), label="ijro boshlandi")

    async def pause(self, browser: str) -> Result:
        if await self._is_playing(browser) is False:
            return True, "YouTube: allaqachon pauzada"
        return await self._youtube(browser, ("k", 1), label="pauza qilindi")

    async def seek(self, browser: str, seconds: float) -> Result:
        presses = seek_presses(float(seconds or 0))
        if not presses:
            return True, "YouTube: siljish 0 s"
        word = "oldinga" if float(seconds) > 0 else "orqaga"
        return await self._youtube(browser, *presses, label=f"{abs(round(float(seconds)))} s {word}")

    async def seek_to(self, browser: str, seconds: float) -> Result:
        return await self._youtube(browser, ("0", 1), *seek_presses(float(seconds or 0)), label=f"{int(float(seconds or 0))} s ga o'tildi")

    async def restart(self, browser: str) -> Result:
        return await self._youtube(browser, ("0", 1), label="boshidan boshlandi")

    async def set_player_volume(self, browser: str, level: float) -> Result:
        lvl = max(0, min(100, int(float(level))))
        return await self._youtube(
            browser, ("down", 100 // YOUTUBE_VOLUME_STEP), ("up", round(lvl / YOUTUBE_VOLUME_STEP)), label=f"ovoz {lvl}%"
        )

    async def toggle_mute(self, browser: str) -> Result:
        return await self._youtube(browser, ("m", 1), label="ovoz o'chirildi/yoqildi")

    async def set_playback_rate(self, browser: str, rate: float) -> Result:
        r = max(0.25, min(2.0, float(rate or 1.0)))
        return await self._youtube(browser, *speed_presses(r), label=f"tezlik {r:g}x")

    async def toggle_fullscreen(self, browser: str) -> Result:
        return await self._youtube(browser, ("f", 1), label="to'liq ekran almashtirildi")

    async def toggle_subtitles(self, browser: str) -> Result:
        return await self._youtube(browser, ("c", 1), label="subtitrlar almashtirildi")

    async def next_video(self, browser: str) -> Result:
        return await self._youtube(browser, ("shift+n", 1), label="keyingi video")

    async def get_video_info(self, browser: str) -> Result:
        win = await self._window(browser)
        if win is None or "youtube" not in win.title.lower():
            return False, "Faol tab YouTube emas"
        from nexus.windows_screen import _walk

        def work(auto: Any, root: Any) -> str:
            for c in _walk(root, 3000):
                text = (c.Name or "").strip()
                if re.fullmatch(r"\d{1,2}(:\d\d){1,2}\s*/\s*\d{1,2}(:\d\d){1,2}", text):
                    return text
            return ""

        try:
            pos = await self._uia_run(win.hwnd, work)
        except Exception:  # noqa: BLE001
            pos = ""
        title = win.page_title.removesuffix(" - YouTube")
        playing = await self._is_playing(browser)
        state = {True: "ijro etilmoqda", False: "pauzada", None: ""}[playing]
        return True, "; ".join(p for p in (title, pos, state) if p)


__all__ = [
    "BrowserWindow",
    "WindowsBrowser",
    "browser_key",
    "list_browser_windows",
    "looks_like_result",
    "pick_window",
    "seek_presses",
    "speed_presses",
]
