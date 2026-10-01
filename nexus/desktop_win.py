"""Windows desktop qatlami: daemon alohida thread'da, UI — pywebview (Edge WebView2) oynasida.

macOS'dagi `nexus.desktop` (Cocoa + WKWebView) o'rniga. Orb overlay va menyu bar yo'q —
bitta asosiy oyna. Oyna yopilsa daemon to'xtatiladi. pywebview yoki WebView2 bo'lmasa,
UI standart brauzerda ochiladi va daemon Ctrl+C / jarayon tugaguncha ishlaydi.
"""

from __future__ import annotations

import logging
import socket
import time
import webbrowser

from nexus.config import Settings
from nexus.desktop import DaemonRunner, DesktopOptions

log = logging.getLogger("nexus.desktop_win")

WINDOW_TITLE = "Nexus Ovoz OS"
SERVER_WAIT_S = 20.0
LOG_HINT = r"%USERPROFILE%\.nexus\logs\nexus.log"


def show_error(message: str) -> None:
    """Konsolsiz .exe da xato ko'rinmay qolmasin — Windows xabar oynasi."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, WINDOW_TITLE, 0x10)  # MB_ICONERROR
    except (AttributeError, OSError):
        log.error("%s", message)


def wait_for_port(host: str, port: int, timeout: float = SERVER_WAIT_S) -> bool:
    """UI serveri tinglay boshlaguncha kutadi."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def run_desktop(settings: Settings, options: DesktopOptions) -> int:
    runner = DaemonRunner(settings)
    runner.start()
    url = f"http://{settings.ui_host}:{settings.ui_port}/"
    if not wait_for_port(settings.ui_host, settings.ui_port):
        log.error("UI serveri %s da ishga tushmadi", url)
        runner.stop()
        show_error(
            "Nexus ishga tushmadi: UI serveri ochilmadi.\n\n"
            f"Port {settings.ui_port} band bo'lishi mumkin (Nexus allaqachon ochiqmi?).\n"
            f"Batafsil: {LOG_HINT}"
        )
        return runner.exit_code or 1

    if not options.window:
        return _wait_headless(runner)

    try:
        import webview  # pywebview
    except ImportError:
        log.warning("pywebview yo'q — UI brauzerda ochiladi: %s", url)
        webbrowser.open(url)
        return _wait_headless(runner)

    from nexus.windows_video import mark_gui_ready

    main_window = webview.create_window(WINDOW_TITLE, url, width=1180, height=780, min_size=(820, 560))
    # Asosiy oyna yopilsa — video oynasi ham yopiladi va ilova tugaydi
    main_window.events.closed += lambda: [w.destroy() for w in list(webview.windows) if w is not main_window]
    try:
        webview.start(mark_gui_ready)  # oyna yopilguncha bloklaydi
    except Exception as e:  # noqa: BLE001 — WebView2 runtime yo'q va h.k.
        log.error("Oyna ochilmadi (%s) — UI brauzerda ochiladi", e)
        webbrowser.open(url)
        return _wait_headless(runner)
    runner.stop()
    return runner.exit_code or 0


def _wait_headless(runner: DaemonRunner) -> int:
    try:
        while runner.is_alive():
            runner.finished.wait(0.5)
    except KeyboardInterrupt:
        pass
    runner.stop()
    return runner.exit_code or 0
