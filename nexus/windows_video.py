"""Windows: video tarjima uchun YouTube'ni Nexus'ning o'z WebView2 oynasida ochadi.

macOS'da `video_translate` foydalanuvchi brauzeridagi video tabida AppleScript orqali JS bajaradi
(`video.currentTime`, pauza, ovoz). Windows'da begona brauzerga JS kanali yo'q, shuning uchun video
pywebview oynasida ochiladi va JS `evaluate_js` bilan bajariladi. Bu faqat desktop rejimida
(Nexus.exe — pywebview GUI sikli ishlayotganda) mumkin; `desktop_win` GUI tayyor bo'lganda
`mark_gui_ready()` ni chaqiradi.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any

log = logging.getLogger("nexus.windows_video")

WINDOW_TITLE = "Nexus — video tarjima"
EVAL_TIMEOUT_S = 8.0

_gui_ready = threading.Event()


def mark_gui_ready() -> None:
    _gui_ready.set()


def gui_ready() -> bool:
    return _gui_ready.is_set()


class WebViewVideoHost:
    """Bitta video oynasi: ochish (yoki mavjudida yangi URL), JS bajarish, yopilganini kuzatish."""

    def __init__(self) -> None:
        self.window: Any = None

    def _on_closed(self) -> None:
        self.window = None

    async def open(self, url: str) -> tuple[bool, str]:
        if not gui_ready():
            return False, "Video tarjima Windows'da faqat Nexus oynasi ochiq bo'lganda ishlaydi (desktop rejim)"

        def _open() -> None:
            import webview

            if self.window is not None:
                try:
                    self.window.load_url(url)
                    self.window.restore()
                    return
                except Exception as e:  # noqa: BLE001 — oyna yopilgan bo'lishi mumkin
                    log.debug("Eski video oynasi ishlamadi: %s", e)
                    self.window = None
            win = webview.create_window(WINDOW_TITLE, url, width=1100, height=680, min_size=(640, 400))
            win.events.closed += self._on_closed
            self.window = win

        try:
            await asyncio.to_thread(_open)
        except Exception as e:  # noqa: BLE001
            return False, f"Video oynasi ochilmadi: {e}"
        return True, ""

    async def eval(self, js: str) -> tuple[bool, str]:
        win = self.window
        if win is None:
            return False, "Video oynasi yopilgan"
        try:
            res = await asyncio.wait_for(asyncio.to_thread(win.evaluate_js, js), timeout=EVAL_TIMEOUT_S)
        except TimeoutError:
            return False, "Video oynasi javob bermadi"
        except Exception as e:  # noqa: BLE001
            return False, f"JS bajarilmadi: {e}"
        return True, "" if res is None else str(res)


host = WebViewVideoHost()

__all__ = ["WebViewVideoHost", "gui_ready", "host", "mark_gui_ready"]
