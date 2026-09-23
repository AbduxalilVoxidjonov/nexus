"""Desktop ilova qatlami: o'z oynasi, doim tepada turadigan orb va menyu bar ikonkasi.

Brauzer OCHILMAYDI: `ui/` web-interfeysi ilovaning o'z NSWindow'i ichida WKWebView orqali
ko'rsatiladi. Texnologiya — to'g'ridan-to'g'ri pyobjc (AppKit + WebKit); pywebview ishlatilmadi,
chunki orb uchun fokus olmaydigan (NonactivatingPanel, canBecomeKeyWindow=False) shaffof
NSPanel kerak, bu pywebview'da yo'q.

Oqimlar (thread'lar):
    * asosiy thread  — AppKit run loop (NSApplication.run). macOS GUI faqat shu yerda ishlaydi.
    * "nexus-daemon" — `nexus.main.run()` o'z asyncio loop'i bilan (audio + Gemini + FastAPI).

Daemon → GUI: EventBus'ga obuna (daemon loop'ida) → `performSelectorOnMainThread` bilan GUI'ga.
GUI → daemon: `asyncio.run_coroutine_threadsafe(bus.dispatch_command(...), daemon_loop)`.

Sof-Python qismlar (holat→rang/yorliq, pozitsiya saqlash, server tayyorligini kutish,
argv → DesktopOptions) GUI'siz test qilinadi (tests/test_desktop.py); Cocoa qismlari
`HAVE_COCOA` bo'lsa yuklanadi.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import signal
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nexus.config import Settings
from nexus.events import bus as global_bus

log = logging.getLogger("nexus.desktop")

APP_TITLE = "Nexus Ovoz OS"
WINDOW_SIZE = (1320, 900)  # zaxira; default — ekranning 90% (WINDOW_SCREEN_FRACTION)
WINDOW_SCREEN_FRACTION = 0.9
WINDOW_MIN_SIZE = (900, 640)
WINDOW_BG = "#07080a"
ORB_SIZE = (128, 148)  # 120×120 shar + ostidagi yorliq
ORB_MARGIN = 24
DEFAULT_PREFS_PATH = Path("~/.nexus/desktop.json").expanduser()
SERVER_READY_TIMEOUT_S = 30.0
DAEMON_STOP_TIMEOUT_S = 5.0

# Holat → rang / yorliq (ui/orb.html bilan bir xil)
STATE_COLORS: dict[str, str] = {
    "idle": "#6b7280",
    "listening": "#22c55e",
    "processing": "#f59e0b",
    "tool_executing": "#34d399",
    "speaking": "#06b6d4",
    "dictating": "#a855f7",
    "awaiting_confirmation": "#f59e0b",
    "connecting": "#6b7280",
    "disconnected": "#ef4444",
    "stopped": "#ef4444",
}
STATE_LABELS: dict[str, str] = {
    "idle": "Kutmoqda",
    "listening": "Tinglamoqda",
    "processing": "O'ylamoqda",
    "tool_executing": "Bajarmoqda",
    "speaking": "Gapirmoqda",
    "dictating": "Yozib turibdi",
    "awaiting_confirmation": "Tasdiq kutilmoqda",
    "connecting": "Ulanmoqda…",
    "disconnected": "Ulanmagan",
    "stopped": "Daemon to'xtagan",
}
# GUI'ga uzatiladigan hodisalar (qolganlari — AUDIO_LEVEL, METRICS — faqat web UI/orb uchun)
FORWARDED_EVENTS = frozenset({"STATE_CHANGE", "CONNECTION", "SETTINGS", "CONFIRM_REQUEST", "CONFIRM_RESOLVED"})


# ---------------------------------------------------------------------------
# Sof-Python qism (GUI'siz test qilinadi)
# ---------------------------------------------------------------------------
def effective_state(
    state: str,
    *,
    gemini: str = "connected",
    pending_confirm: bool = False,
    daemon_alive: bool = True,
) -> str:
    """Daemon holati + Gemini ulanishi + tasdiqdan bitta ko'rsatiladigan holat."""
    if not daemon_alive:
        return "stopped"
    if gemini != "connected":
        return "connecting" if gemini == "reconnecting" else "disconnected"
    if pending_confirm:
        return "awaiting_confirmation"
    return state if state in STATE_COLORS else "idle"


def state_style(state: str, **kw: Any) -> tuple[str, str]:
    """(rang, yorliq) — menyu bar / orb uchun."""
    eff = effective_state(state, **kw)
    return STATE_COLORS[eff], STATE_LABELS[eff]


def status_title(state: str, *, muted: bool = False, **kw: Any) -> str:
    """Menyu bar'dagi holat satri, masalan "● Tinglamoqda" yoki "● Kutmoqda (mikrofon o'chiq)"."""
    _, label = state_style(state, **kw)
    return f"● {label}" + (" (mikrofon o'chiq)" if muted else "")


@dataclass
class DesktopOptions:
    window: bool = True
    orb: bool = True
    hide_dock: bool = False

    @classmethod
    def from_args(cls, args: Any) -> DesktopOptions:
        """argparse Namespace (nexus.main.build_parser) → DesktopOptions."""
        return cls(
            window=not getattr(args, "no_window", False),
            orb=not getattr(args, "no_orb", False),
            hide_dock=_env_true("NEXUS_HIDE_DOCK"),
        )


def _env_true(name: str) -> bool:
    return (os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


class DesktopPrefs:
    """~/.nexus/desktop.json — orb pozitsiyasi, oyna o'lchami, orb ko'rinishi."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_PREFS_PATH
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (OSError, ValueError):
            return {}

    def save(self) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)
            return True
        except OSError as e:
            log.debug("desktop.json saqlanmadi: %s", e)
            return False

    # --- orb ---
    @property
    def orb_position(self) -> tuple[float, float] | None:
        return _pair(self.data.get("orb"), "x", "y")

    def set_orb_position(self, x: float, y: float) -> None:
        self.data["orb"] = {"x": round(float(x), 1), "y": round(float(y), 1)}

    @property
    def orb_visible(self) -> bool:
        return bool(self.data.get("orb_visible", True))

    def set_orb_visible(self, visible: bool) -> None:
        self.data["orb_visible"] = bool(visible)

    # --- oyna ---
    @property
    def window_frame(self) -> tuple[float, float, float, float] | None:
        w = self.data.get("window")
        if not isinstance(w, dict):
            return None
        try:
            frame = tuple(float(w[k]) for k in ("x", "y", "w", "h"))
        except (KeyError, TypeError, ValueError):
            return None
        return frame if frame[2] >= 200 and frame[3] >= 200 else None

    def set_window_frame(self, x: float, y: float, w: float, h: float) -> None:
        self.data["window"] = {"x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1)}


def _pair(obj: Any, kx: str, ky: str) -> tuple[float, float] | None:
    if not isinstance(obj, dict):
        return None
    try:
        return float(obj[kx]), float(obj[ky])
    except (KeyError, TypeError, ValueError):
        return None


Rect = tuple[float, float, float, float]  # x, y, w, h (Cocoa: boshlang'ich nuqta pastki-chap)


def rect_on_screens(rect: Rect, screens: list[Rect], min_visible: float = 40.0) -> bool:
    """Oyna/orb hech bo'lmaganda `min_visible`×`min_visible` qismi bilan biror ekranda ko'rinadimi?"""
    x, y, w, h = rect
    for sx, sy, sw, sh in screens:
        ox = min(x + w, sx + sw) - max(x, sx)
        oy = min(y + h, sy + sh) - max(y, sy)
        if ox >= min(min_visible, w) and oy >= min(min_visible, h):
            return True
    return False


def default_orb_origin(visible_frame: Rect, size: tuple[float, float] = ORB_SIZE, margin: float = ORB_MARGIN):
    """Ekranning pastki-o'ng burchagi (Dock/menyu bar hisobga olingan `visibleFrame` ichida)."""
    sx, sy, sw, _sh = visible_frame
    return (sx + sw - size[0] - margin, sy + margin)


def default_window_frame(
    visible_frame: Rect, size: tuple[float, float] | None = None, fraction: float = WINDOW_SCREEN_FRACTION
) -> Rect:
    """Ekran o'rtasida, `visibleFrame`ning `fraction` (90%) qismi (yoki `size`), min o'lchamdan kam emas."""
    sx, sy, sw, sh = visible_frame
    want = size or (sw * fraction, sh * fraction)
    w = max(min(want[0], sw), min(WINDOW_MIN_SIZE[0], sw))
    h = max(min(want[1], sh), min(WINDOW_MIN_SIZE[1], sh))
    return (sx + (sw - w) / 2, sy + (sh - h) / 2, w, h)


def _http_ok(url: str, timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError, ValueError):
        return False


def wait_for_server(
    base_url: str,
    timeout: float = SERVER_READY_TIMEOUT_S,
    interval: float = 0.25,
    *,
    probe: Callable[[str], bool] | None = None,
    keep_waiting: Callable[[], bool] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> bool:
    """`base_url/health` 2xx qaytarguncha kutadi.

    `keep_waiting()` False qaytarsa (daemon o'ldi) darhol False. Testlarda `probe`/`sleep`/`clock`
    almashtiriladi.
    """
    probe = probe or _http_ok
    url = base_url.rstrip("/") + "/health"
    deadline = clock() + timeout
    while True:
        if probe(url):
            return True
        if keep_waiting is not None and not keep_waiting():
            return False
        if clock() >= deadline:
            return False
        sleep(interval)


def placeholder_html(title: str, detail: str = "", spinner: bool = True) -> str:
    """Server tayyor bo'lguncha (yoki daemon xato bilan to'xtasa) oynada ko'rsatiladigan sahifa."""
    spin = (
        '<div class="spin"></div>'
        if spinner
        else '<div class="err">!</div>'
    )
    return f"""<!DOCTYPE html><html lang="uz"><head><meta charset="utf-8"><style>
html,body{{margin:0;height:100%;background:{WINDOW_BG};color:#e4e8ec;
font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text",system-ui,sans-serif;-webkit-user-select:none}}
body{{display:flex;align-items:center;justify-content:center;text-align:center}}
.spin{{width:28px;height:28px;border-radius:50%;border:3px solid rgba(255,255,255,.12);
border-top-color:#22d3ee;animation:s 1s linear infinite;margin:0 auto 18px}}
.err{{width:34px;height:34px;border-radius:50%;background:#ef4444;color:#fff;font-weight:700;
line-height:34px;margin:0 auto 18px}}
@keyframes s{{to{{transform:rotate(360deg)}}}}
h1{{font-size:15px;font-weight:600;margin:0 0 8px}}p{{font-size:12px;color:#949ba3;margin:0;
white-space:pre-wrap;max-width:520px;font-family:"JetBrains Mono",Menlo,monospace}}
</style></head><body><div>{spin}<h1>{title}</h1><p>{detail}</p></div></body></html>"""


# ---------------------------------------------------------------------------
# Daemon thread (asyncio loop alohida thread'da)
# ---------------------------------------------------------------------------
class DaemonRunner:
    """`nexus.main.run()` ni alohida thread'da o'z event loop'i bilan yuritadi."""

    def __init__(self, settings: Settings, on_event: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.settings = settings
        self.on_event = on_event
        self.loop: asyncio.AbstractEventLoop | None = None
        self.stop_event: asyncio.Event | None = None
        self.exit_code: int | None = None
        self.error: BaseException | None = None
        self.started = threading.Event()
        self.finished = threading.Event()
        self.thread = threading.Thread(target=self._main, name="nexus-daemon", daemon=True)

    # --- hayot sikli ---
    def start(self) -> None:
        self.thread.start()
        self.started.wait(timeout=5.0)

    def is_alive(self) -> bool:
        return self.thread.is_alive() and not self.finished.is_set()

    def _main(self) -> None:
        from nexus.main import run as daemon_run

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        self.stop_event = asyncio.Event()
        forward = loop.create_task(self._forward_events(), name="desktop-bridge")
        self.started.set()
        try:
            self.exit_code = loop.run_until_complete(
                daemon_run(self.settings, ui=True, stop_event=self.stop_event, install_signals=False)
            )
        except Exception as e:
            self.error = e
            self.exit_code = 1
            log.exception("Daemon xato bilan tugadi")
        finally:
            forward.cancel()
            try:
                loop.run_until_complete(asyncio.gather(forward, return_exceptions=True))
                loop.run_until_complete(loop.shutdown_asyncgens())
            except Exception as e:  # noqa: BLE001
                log.debug("Loop yopishda xato: %s", e)
            loop.close()
            self.finished.set()

    def request_stop(self) -> None:
        """To'xtatish signalini beradi (bloklamaydi) — tugashini `finished` orqali kuzatish mumkin."""
        loop, ev = self.loop, self.stop_event
        if loop is not None and ev is not None and not loop.is_closed():
            try:
                loop.call_soon_threadsafe(ev.set)
            except RuntimeError:
                pass

    def stop(self, timeout: float = DAEMON_STOP_TIMEOUT_S) -> bool:
        """To'xtatish signalini beradi va thread tugashini kutadi. True = toza tugadi."""
        self.request_stop()
        self.thread.join(timeout)
        if self.thread.is_alive():
            log.warning("Daemon thread %.0f s ichida tugamadi", timeout)
            return False
        return True

    # --- ko'prik ---
    def dispatch(self, msg: dict[str, Any]) -> None:
        """GUI'dan daemon'ga buyruq (thread-safe, natija kutilmaydi)."""
        loop = self.loop
        if loop is None or loop.is_closed() or not self.is_alive():
            log.warning("Daemon ishlamayapti, buyruq tashlab yuborildi: %s", msg.get("cmd"))
            return
        fut = asyncio.run_coroutine_threadsafe(global_bus.dispatch_command(msg), loop)

        def _done(f: Any) -> None:
            try:
                res = f.result()
                if isinstance(res, dict) and not res.get("ok", True):
                    log.warning("Buyruq bajarilmadi: %s → %s", msg.get("cmd"), res.get("error"))
            except Exception as e:  # noqa: BLE001
                log.warning("Buyruq xatosi (%s): %s", msg.get("cmd"), e)

        fut.add_done_callback(_done)

    async def _forward_events(self) -> None:
        q = global_bus.subscribe()
        try:
            while True:
                ev = await q.get()
                if self.on_event is not None and ev.get("type") in FORWARDED_EVENTS:
                    try:
                        self.on_event(ev)
                    except Exception as e:  # noqa: BLE001
                        log.debug("Hodisa GUI'ga uzatilmadi: %s", e)
        finally:
            global_bus.unsubscribe(q)


# ---------------------------------------------------------------------------
# Cocoa qismi
# ---------------------------------------------------------------------------
HAVE_COCOA = False
if sys.platform == "darwin":
    try:
        import objc
        from AppKit import (
            NSApp,
            NSApplication,
            NSApplicationActivationPolicyAccessory,
            NSApplicationActivationPolicyRegular,
            NSBackingStoreBuffered,
            NSColor,
            NSEvent,
            NSEventTypeApplicationDefined,
            NSEventTypeLeftMouseDown,
            NSEventTypeLeftMouseDragged,
            NSEventTypeLeftMouseUp,
            NSEventTypeRightMouseDown,
            NSFloatingWindowLevel,
            NSImage,
            NSMenu,
            NSMenuItem,
            NSPanel,
            NSScreen,
            NSStatusBar,
            NSTerminateCancel,
            NSTimer,
            NSVariableStatusItemLength,
            NSViewHeightSizable,
            NSViewWidthSizable,
            NSWindow,
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorFullScreenPrimary,
            NSWindowCollectionBehaviorStationary,
            NSWindowStyleMaskBorderless,
            NSWindowStyleMaskClosable,
            NSWindowStyleMaskFullSizeContentView,
            NSWindowStyleMaskMiniaturizable,
            NSWindowStyleMaskNonactivatingPanel,
            NSWindowStyleMaskResizable,
            NSWindowStyleMaskTitled,
            NSWindowTitleHidden,
            NSWorkspace,
        )
        from Foundation import NSURL, NSBundle, NSObject, NSURLRequest
        from WebKit import WKWebView, WKWebViewConfiguration

        HAVE_COCOA = True
    except ImportError as _e:  # pragma: no cover
        log.debug("Cocoa yuklanmadi: %s", _e)


def _hex_color(hex_str: str) -> Any:
    h = hex_str.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, 1.0)


def _make_webview(frame: Any, *, transparent: bool, bg: str = WINDOW_BG, message_handler: Any = None) -> Any:
    cfg = WKWebViewConfiguration.alloc().init()
    if message_handler is not None:
        # JS: window.webkit.messageHandlers.nexus.postMessage({type: "drag"|"zoom"})
        cfg.userContentController().addScriptMessageHandler_name_(message_handler, "nexus")
    wv = WKWebView.alloc().initWithFrame_configuration_(frame, cfg)
    wv.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
    if transparent:
        try:
            wv.setValue_forKey_(False, "drawsBackground")  # shaffof WKWebView (pywebview ham shunday qiladi)
        except Exception as e:  # noqa: BLE001
            log.debug("drawsBackground o'rnatilmadi: %s", e)
    try:
        wv.setUnderPageBackgroundColor_(NSColor.clearColor() if transparent else _hex_color(bg))
    except Exception as e:  # noqa: BLE001
        log.debug("underPageBackgroundColor o'rnatilmadi: %s", e)
    return wv


def _load_url(webview: Any, url: str) -> None:
    # 1 = NSURLRequestReloadIgnoringLocalCacheData: UI fayllari yangilanganda eski kesh ishlatilmasin
    req = NSURLRequest.requestWithURL_cachePolicy_timeoutInterval_(NSURL.URLWithString_(url), 1, 30.0)
    webview.loadRequest_(req)


def _set_process_display_name(name: str) -> None:
    """Ilova menyusida (chap yuqori) "python" o'rniga ilova nomi (bundle'siz ishga tushganda)."""
    try:
        info = NSBundle.mainBundle().infoDictionary()
        if info is not None:
            info["CFBundleName"] = name
            info["CFBundleDisplayName"] = name
    except Exception as e:  # noqa: BLE001
        log.debug("CFBundleName o'rnatilmadi: %s", e)


def _make_app_icon(size: float = 256.0) -> Any:
    """Dock uchun oddiy ikonka: qorong'i doira ichida moviy shar (bundle'siz — python raketasi o'rniga)."""
    try:
        from AppKit import NSBezierPath, NSGradient

        img = NSImage.alloc().initWithSize_((size, size))
        img.lockFocus()
        pad = size * 0.06
        bg = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            ((pad, pad), (size - 2 * pad, size - 2 * pad)), size * 0.22, size * 0.22
        )
        _hex_color("#0f1216").setFill()
        bg.fill()
        r = size * 0.27
        c = size / 2
        orb = NSBezierPath.bezierPathWithOvalInRect_(((c - r, c - r), (2 * r, 2 * r)))
        grad = NSGradient.alloc().initWithStartingColor_endingColor_(_hex_color("#7dd3fc"), _hex_color("#0e7490"))
        grad.drawInBezierPath_angle_(orb, -60.0)
        img.unlockFocus()
        return img
    except Exception as e:  # noqa: BLE001
        log.debug("Dock ikonkasi chizilmadi: %s", e)
        return None


if HAVE_COCOA:

    class NexusOrbPanel(NSPanel):
        """Ramkasiz, shaffof, doim tepada, klaviatura fokusini OLMAYDIGAN panel.

        Sichqoncha hodisalari `sendEvent:` da ushlanadi (surish, bir/ikki marta bosish, o'ng tugma),
        ichidagi WKWebView'ga yetib bormaydi — orb.html faqat ko'rsatish uchun.
        """

        controller = objc.ivar()

        def canBecomeKeyWindow(self) -> bool:
            return False

        def canBecomeMainWindow(self) -> bool:
            return False

        def sendEvent_(self, event: Any) -> None:
            t = event.type()
            ctl = self.controller
            if ctl is None or t not in (
                NSEventTypeLeftMouseDown,
                NSEventTypeLeftMouseDragged,
                NSEventTypeLeftMouseUp,
                NSEventTypeRightMouseDown,
            ):
                objc.super(NexusOrbPanel, self).sendEvent_(event)
                return
            try:
                if t == NSEventTypeLeftMouseDown:
                    ctl.orbMouseDown_(event)
                elif t == NSEventTypeLeftMouseDragged:
                    ctl.orbMouseDragged_(event)
                elif t == NSEventTypeLeftMouseUp:
                    ctl.orbMouseUp_(event)
                else:
                    ctl.orbRightClick_(event)
            except Exception:
                log.exception("Orb sichqoncha hodisasi")

    class NexusDesktopApp(NSObject):
        """NSApplication delegati: oyna, orb, menyu bar, daemon ko'prigi."""

        # --- init ---
        def initWithSettings_options_prefs_(  # pyobjc init shabloni: self qayta tayinlanadi
            self, settings: Settings, options: DesktopOptions, prefs: DesktopPrefs
        ):
            self = objc.super(NexusDesktopApp, self).init()  # noqa: PLW0642
            if self is None:
                return None
            self.settings = settings
            self.options = options
            self.prefs = prefs
            self.runner = DaemonRunner(settings, on_event=self.post_event)
            self.base_url = f"http://{settings.ui_host}:{settings.ui_port}"
            self.window: Any = None
            self.web: Any = None
            self.orb: Any = None
            self.orb_web: Any = None
            self.status_item: Any = None
            self.menu: Any = None
            self.items: dict[str, Any] = {}
            self.exit_code = 0
            self.daemon_clean = True
            self._quitting = False
            self._shutdown_deadline = 0.0
            self._server_ready = False
            # holat
            self.state = "idle"
            self.gemini = "disconnected"
            self.muted = False
            self.dictating = False
            self.confirm_pending = False
            # orb surish
            self._drag_offset: tuple[float, float] | None = None
            self._dragged = False
            return self

        # --- NSApplicationDelegate ---
        def applicationDidFinishLaunching_(self, _n: Any) -> None:
            try:
                self._build_main_menu()
                self._build_status_item()
                self._build_window()
                self._build_orb()
                self._install_signals()
                self.runner.start()
                threading.Thread(target=self._wait_ready, name="nexus-ready-poll", daemon=True).start()
                if self.options.window:
                    self.showWindow_(None)
                if self.options.orb and self.prefs.orb_visible:
                    self._show_orb()
                self._refresh_status()
            except Exception:
                log.exception("Desktop ishga tushmadi")
                self.exit_code = 1
                self._quit_now()

        def applicationShouldTerminate_(self, _sender: Any) -> int:
            # Cmd+Q / menyu "Chiqish" / SIGINT — hammasi shu yerga keladi.
            # Terminate bekor qilinadi: to'xtatish o'zimizda — run loop ishlashda davom etadi (asosiy thread
            # bloklanmaydi — CoreAudio HAL asosiy run loop'ga muhtoj, join() bilan kutish PortAudio stop'ni
            # deadlock'ka olib keladi), daemon tugagach NSApp().run() qaytadi va Python toza chiqadi.
            self._begin_shutdown()
            return NSTerminateCancel

        def applicationShouldHandleReopen_hasVisibleWindows_(self, _app: Any, _flag: bool) -> bool:
            self.showWindow_(None)  # Dock ikonkasi bosilganda
            return False

        # --- NSWindowDelegate (asosiy oyna) ---
        def windowShouldClose_(self, _sender: Any) -> bool:
            self._save_window_frame()
            self.window.orderOut_(None)
            return False  # yopilmaydi — yashirinadi; dastur ishlashda davom etadi

        def windowDidEnterFullScreen_(self, _n: Any) -> None:
            self._set_fullscreen_class(True)

        def windowDidExitFullScreen_(self, _n: Any) -> None:
            self._set_fullscreen_class(False)

        def _set_fullscreen_class(self, on: bool) -> None:
            # To'liq ekranda macOS tugmalari yo'q — UI sarlavhasidagi chap bo'sh joy olib tashlanadi
            if self.web is not None:
                js = f"document.body.classList.toggle('nx-fullscreen', {'true' if on else 'false'})"
                self.web.evaluateJavaScript_completionHandler_(js, None)

        # --- WKScriptMessageHandler (web UI → native) ---
        def userContentController_didReceiveScriptMessage_(self, _ucc: Any, message: Any) -> None:
            body = message.body()
            kind = body.get("type") if isinstance(body, dict) else str(body)
            if self.window is None:
                return
            if kind == "drag":
                ev = NSApp().currentEvent()
                if ev is not None:
                    self.window.performWindowDragWithEvent_(ev)
            elif kind == "zoom":
                self.window.zoom_(None)

        # --- qurish ---
        def _build_main_menu(self) -> None:
            main = NSMenu.alloc().init()

            app_item = NSMenuItem.alloc().init()
            app_menu = NSMenu.alloc().initWithTitle_(APP_TITLE)
            app_menu.addItemWithTitle_action_keyEquivalent_("Oynani ko'rsatish", "showWindow:", "1").setTarget_(self)
            app_menu.addItem_(NSMenuItem.separatorItem())
            app_menu.addItemWithTitle_action_keyEquivalent_(f"{APP_TITLE} ni yashirish", "hide:", "h")
            app_menu.addItem_(NSMenuItem.separatorItem())
            app_menu.addItemWithTitle_action_keyEquivalent_("Chiqish", "terminate:", "q")
            app_item.setSubmenu_(app_menu)
            main.addItem_(app_item)

            edit_item = NSMenuItem.alloc().init()
            edit_menu = NSMenu.alloc().initWithTitle_("Tahrir")
            for title, sel, key in (
                ("Bekor qilish", "undo:", "z"),
                ("Qaytarish", "redo:", "Z"),
                ("Kesish", "cut:", "x"),
                ("Nusxalash", "copy:", "c"),
                ("Qo'yish", "paste:", "v"),
                ("Hammasini tanlash", "selectAll:", "a"),
            ):
                edit_menu.addItemWithTitle_action_keyEquivalent_(title, sel, key)
            edit_item.setSubmenu_(edit_menu)
            main.addItem_(edit_item)

            win_item = NSMenuItem.alloc().init()
            win_menu = NSMenu.alloc().initWithTitle_("Oyna")
            win_menu.addItemWithTitle_action_keyEquivalent_("Yopish", "performClose:", "w")
            win_menu.addItemWithTitle_action_keyEquivalent_("Kichraytirish", "performMiniaturize:", "m")
            win_item.setSubmenu_(win_menu)
            main.addItem_(win_item)
            NSApp().setMainMenu_(main)
            NSApp().setWindowsMenu_(win_menu)

        def _build_status_item(self) -> None:
            self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
            btn = self.status_item.button()
            img = None
            try:
                img = NSImage.imageWithSystemSymbolName_accessibilityDescription_("waveform", APP_TITLE)
            except Exception as e:  # noqa: BLE001
                log.debug("SF Symbol yuklanmadi: %s", e)
            if img is not None:
                img.setTemplate_(True)
                btn.setImage_(img)
            else:
                btn.setTitle_("◉")
            btn.setToolTip_(APP_TITLE)

            menu = NSMenu.alloc().initWithTitle_(APP_TITLE)
            menu.setAutoenablesItems_(False)

            def add(key: str, title: str, sel: str | None, key_eq: str = "") -> Any:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, sel, key_eq)
                if sel:
                    item.setTarget_(self)
                else:
                    item.setEnabled_(False)
                menu.addItem_(item)
                self.items[key] = item
                return item

            add("status", "● Ishga tushmoqda…", None)
            menu.addItem_(NSMenuItem.separatorItem())
            add("window", "Oynani ko'rsatish", "showWindow:")
            add("orb", "Orb yashirish", "toggleOrb:")
            menu.addItem_(NSMenuItem.separatorItem())
            add("mute", "Mikrofonni o'chirish", "toggleMute:")
            add("dictation", "Diktovka", "toggleDictation:")
            add("kill", "Hammasini to'xtatish", "killAll:")
            menu.addItem_(NSMenuItem.separatorItem())
            add("env", "Sozlamalar (.env)", "openEnv:")
            add("quit", "Chiqish", "quit:", "q")
            self.status_item.setMenu_(menu)
            self.menu = menu

        def _visible_frame(self) -> Rect:
            screen = NSScreen.mainScreen() or (NSScreen.screens() or [None])[0]
            if screen is None:
                return (0.0, 0.0, 1440.0, 900.0)
            f = screen.visibleFrame()
            return (f.origin.x, f.origin.y, f.size.width, f.size.height)

        def _screens(self) -> list[Rect]:
            out: list[Rect] = []
            for s in NSScreen.screens() or []:
                f = s.frame()
                out.append((f.origin.x, f.origin.y, f.size.width, f.size.height))
            return out

        def _build_window(self) -> None:
            frame = self.prefs.window_frame
            if frame is None or not rect_on_screens(frame, self._screens()):
                frame = default_window_frame(self._visible_frame())
            x, y, w, h = frame
            style = (
                NSWindowStyleMaskTitled
                | NSWindowStyleMaskClosable
                | NSWindowStyleMaskMiniaturizable
                | NSWindowStyleMaskResizable
                | NSWindowStyleMaskFullSizeContentView  # web UI titlebar ostigacha cho'ziladi
            )
            win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                ((x, y), (w, h)), style, NSBackingStoreBuffered, False
            )
            win.setTitle_(APP_TITLE)
            win.setReleasedWhenClosed_(False)
            win.setContentMinSize_(WINDOW_MIN_SIZE)
            win.setBackgroundColor_(_hex_color(WINDOW_BG))
            # Haqiqiy macOS tugmalari (yopish/kichraytirish/to'liq ekran) UI sarlavhasi ustida; sarlavha matni yashirin
            win.setTitlebarAppearsTransparent_(True)
            win.setTitleVisibility_(NSWindowTitleHidden)
            win.setCollectionBehavior_(NSWindowCollectionBehaviorFullScreenPrimary)  # yashil tugma = to'liq ekran
            try:
                # Bo'sh toolbar: titlebar balandroq (~52px) bo'lib, tugmalar UI sarlavhasi bilan markazlashadi
                from AppKit import NSTitlebarSeparatorStyleNone, NSToolbar, NSWindowToolbarStyleUnified

                toolbar = NSToolbar.alloc().initWithIdentifier_("nexus-main-toolbar")
                toolbar.setShowsBaselineSeparator_(False)
                win.setToolbar_(toolbar)
                win.setToolbarStyle_(NSWindowToolbarStyleUnified)
                win.setTitlebarSeparatorStyle_(NSTitlebarSeparatorStyleNone)
            except Exception as e:  # noqa: BLE001
                log.debug("Toolbar hiylasi ishlamadi: %s", e)
            try:
                from AppKit import NSAppearance, NSAppearanceNameDarkAqua

                win.setAppearance_(NSAppearance.appearanceNamed_(NSAppearanceNameDarkAqua))
            except Exception as e:  # noqa: BLE001
                log.debug("Dark appearance o'rnatilmadi: %s", e)
            win.setDelegate_(self)
            self.web = _make_webview(((0, 0), (w, h)), transparent=False, message_handler=self)
            win.setContentView_(self.web)
            self.web.loadHTMLString_baseURL_(
                placeholder_html("Nexus ishga tushmoqda…", "audio · Gemini · UI serveri"), None
            )
            self.window = win

        def _build_orb(self) -> None:
            w, h = ORB_SIZE
            pos = self.prefs.orb_position
            if pos is None or not rect_on_screens((pos[0], pos[1], w, h), self._screens()):
                pos = default_orb_origin(self._visible_frame())
            panel = NexusOrbPanel.alloc().initWithContentRect_styleMask_backing_defer_(
                ((pos[0], pos[1]), (w, h)),
                NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
                NSBackingStoreBuffered,
                False,
            )
            panel.controller = self
            panel.setLevel_(NSFloatingWindowLevel + 1)
            panel.setOpaque_(False)
            panel.setBackgroundColor_(NSColor.clearColor())
            panel.setHasShadow_(False)
            panel.setHidesOnDeactivate_(False)
            panel.setMovableByWindowBackground_(False)  # surishni o'zimiz boshqaramiz
            panel.setReleasedWhenClosed_(False)
            panel.setCollectionBehavior_(
                NSWindowCollectionBehaviorCanJoinAllSpaces
                | NSWindowCollectionBehaviorFullScreenAuxiliary
                | NSWindowCollectionBehaviorStationary
            )
            panel.setTitle_("Nexus orb")
            self.orb_web = _make_webview(((0, 0), (w, h)), transparent=True)
            panel.setContentView_(self.orb_web)
            self.orb = panel

        def _install_signals(self) -> None:
            """SIGINT/SIGTERM → toza chiqish. Mach-port orqali AppKit run loop'ida qayta ishlanadi."""
            try:
                from PyObjCTools import MachSignals

                for sig in (signal.SIGINT, signal.SIGTERM):
                    MachSignals.signal(sig, self._on_signal)
            except Exception as e:  # noqa: BLE001
                log.warning("Signal handlerlari o'rnatilmadi: %s", e)

        def _on_signal(self, signum: int) -> None:
            try:
                name = signal.Signals(signum).name
            except ValueError:
                name = str(signum)
            log.info("Signal olindi: %s — to'xtatilmoqda", name)
            self.quit_(None)

        # --- server tayyorligi ---
        def _wait_ready(self) -> None:
            ok = wait_for_server(self.base_url, keep_waiting=self.runner.is_alive)
            self.performSelectorOnMainThread_withObject_waitUntilDone_("serverReady:", "ok" if ok else "fail", False)

        def serverReady_(self, result: Any) -> None:
            if str(result) == "ok":
                self._server_ready = True
                log.info("UI serveri tayyor — oyna va orb yuklanmoqda: %s", self.base_url)
                _load_url(self.web, self.base_url + "/")
                _load_url(self.orb_web, self.base_url + "/orb")
            else:
                alive = self.runner.is_alive()
                detail = (
                    f"UI serveri {int(SERVER_READY_TIMEOUT_S)} s ichida javob bermadi ({self.base_url})."
                    if alive
                    else "Daemon to'xtadi. Terminal/log'ga qarang (masalan, GEMINI_API_KEY bo'sh yoki port band)."
                )
                if self.runner.error is not None:
                    detail += f"\n{type(self.runner.error).__name__}: {self.runner.error}"
                log.error("Server tayyor bo'lmadi: %s", detail)
                self.web.loadHTMLString_baseURL_(placeholder_html("Nexus ishga tushmadi", detail, spinner=False), None)
                if self.options.window:
                    self.showWindow_(None)
            self._refresh_status()

        # --- daemon → GUI ---
        def post_event(self, ev: dict[str, Any]) -> None:
            """Daemon thread'idan chaqiriladi — hodisani GUI thread'iga uzatadi."""
            payload = json.dumps(ev, ensure_ascii=False, default=str)
            self.performSelectorOnMainThread_withObject_waitUntilDone_("handleEvent:", payload, False)

        def handleEvent_(self, payload: Any) -> None:
            try:
                ev = json.loads(str(payload))
            except ValueError:
                return
            t, d = ev.get("type"), ev.get("data") or {}
            if t == "STATE_CHANGE":
                self.state = d.get("state", self.state)
            elif t == "CONNECTION":
                self.gemini = d.get("gemini", self.gemini)
            elif t == "SETTINGS":
                if "muted" in d:
                    self.muted = bool(d["muted"])
                if "dictating" in d:
                    self.dictating = bool(d["dictating"])
            elif t == "CONFIRM_REQUEST":
                self.confirm_pending = True
            elif t == "CONFIRM_RESOLVED":
                self.confirm_pending = False
            self._refresh_status()

        def _refresh_status(self) -> None:
            if not self.items:
                return
            alive = self.runner.is_alive()
            if not self._server_ready and alive:
                title = "● Ishga tushmoqda…"
            else:
                title = status_title(
                    self.state,
                    muted=self.muted,
                    gemini=self.gemini,
                    pending_confirm=self.confirm_pending,
                    daemon_alive=alive,
                )
            self.items["status"].setTitle_(title)
            self.items["mute"].setTitle_("Mikrofonni yoqish" if self.muted else "Mikrofonni o'chirish")
            self.items["dictation"].setTitle_("Diktovkani to'xtatish" if self.dictating else "Diktovka")
            orb_shown = self.orb is not None and self.orb.isVisible()
            self.items["orb"].setTitle_("Orb yashirish" if orb_shown else "Orb ko'rsatish")
            self.items["orb"].setEnabled_(self.orb is not None)
            for k in ("mute", "dictation", "kill"):
                self.items[k].setEnabled_(alive)
            if self.status_item is not None:
                self.status_item.button().setToolTip_(f"{APP_TITLE} — {title.lstrip('● ')}")

        # --- menyu amallari ---
        def showWindow_(self, _sender: Any) -> None:
            if self.window is None:
                return
            self.window.makeKeyAndOrderFront_(None)
            try:
                NSApp().activateIgnoringOtherApps_(True)
            except Exception as e:  # noqa: BLE001
                log.debug("activate: %s", e)

        def toggleWindow_(self, _sender: Any) -> None:
            if self.window is not None and self.window.isVisible() and NSApp().isActive():
                self._save_window_frame()
                self.window.orderOut_(None)
            else:
                self.showWindow_(None)

        def toggleOrb_(self, _sender: Any) -> None:
            if self.orb is None:
                return
            if self.orb.isVisible():
                self.orb.orderOut_(None)
                self.prefs.set_orb_visible(False)
            else:
                self._show_orb()
                self.prefs.set_orb_visible(True)
            self.prefs.save()
            self._refresh_status()

        def _show_orb(self) -> None:
            if self.orb is not None:
                self.orb.orderFrontRegardless()  # fokus/aktivatsiyasiz ko'rsatish

        def toggleMute_(self, _sender: Any) -> None:
            self.runner.dispatch({"cmd": "mute", "value": not self.muted})

        def toggleDictation_(self, _sender: Any) -> None:
            self.runner.dispatch({"cmd": "dictation", "value": not self.dictating})

        def killAll_(self, _sender: Any) -> None:
            self.runner.dispatch({"cmd": "kill_all"})

        def openEnv_(self, _sender: Any) -> None:
            """`.env` ni Finder'da ko'rsatadi (yagona "tashqi ochish" — brauzer emas)."""
            root = Path(__file__).resolve().parent.parent
            env = root / ".env"
            target = env if env.exists() else root
            NSWorkspace.sharedWorkspace().selectFile_inFileViewerRootedAtPath_(str(target), str(root))

        def quit_(self, _sender: Any) -> None:
            NSApp().terminate_(None)

        # --- orb sichqoncha ---
        def orbMouseDown_(self, _event: Any) -> None:
            loc = NSEvent.mouseLocation()
            origin = self.orb.frame().origin
            self._drag_offset = (loc.x - origin.x, loc.y - origin.y)
            self._dragged = False

        def orbMouseDragged_(self, _event: Any) -> None:
            if self._drag_offset is None:
                return
            loc = NSEvent.mouseLocation()
            self._dragged = True
            self.orb.setFrameOrigin_((loc.x - self._drag_offset[0], loc.y - self._drag_offset[1]))

        def orbMouseUp_(self, event: Any) -> None:
            self._drag_offset = None
            if self._dragged:
                o = self.orb.frame().origin
                self.prefs.set_orb_position(o.x, o.y)
                self.prefs.save()
                return
            clicks = event.clickCount()
            if clicks >= 2:
                NSObject.cancelPreviousPerformRequestsWithTarget_selector_object_(self, "orbSingleClick:", None)
                self.toggleMute_(None)
            elif clicks == 1:
                # Ikkinchi bosish kelmasa — bitta bosish deb qabul qilamiz
                self.performSelector_withObject_afterDelay_("orbSingleClick:", None, NSEvent.doubleClickInterval())

        def orbSingleClick_(self, _obj: Any) -> None:
            self.toggleWindow_(None)

        def orbRightClick_(self, event: Any) -> None:
            if self.menu is not None:
                NSMenu.popUpContextMenu_withEvent_forView_(self.menu, event, self.orb.contentView())

        # --- chiqish ---
        def _save_window_frame(self) -> None:
            if self.window is None:
                return
            f = self.window.frame()
            self.prefs.set_window_frame(f.origin.x, f.origin.y, f.size.width, f.size.height)

        def _begin_shutdown(self) -> None:
            if self._quitting:
                return
            self._quitting = True
            log.info("Desktop yopilmoqda — daemon to'xtatilmoqda…")
            try:
                if self.window is not None and self.window.isVisible():
                    self._save_window_frame()
                if self.orb is not None:
                    o = self.orb.frame().origin
                    self.prefs.set_orb_position(o.x, o.y)
                self.prefs.save()
            except Exception as e:  # noqa: BLE001
                log.debug("Sozlamalar saqlanmadi: %s", e)
            try:
                if self.orb is not None:
                    self.orb.orderOut_(None)
                if self.window is not None:
                    self.window.orderOut_(None)
                if self.status_item is not None:
                    NSStatusBar.systemStatusBar().removeStatusItem_(self.status_item)
                    self.status_item = None
            except Exception as e:  # noqa: BLE001
                log.debug("GUI yopishda xato: %s", e)
            self.runner.request_stop()
            self._shutdown_deadline = time.monotonic() + DAEMON_STOP_TIMEOUT_S
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.1, self, "shutdownTick:", None, True
            )

        def shutdownTick_(self, timer: Any) -> None:
            finished = self.runner.finished.is_set() or not self.runner.thread.is_alive()
            if not finished and time.monotonic() < self._shutdown_deadline:
                return
            timer.invalidate()
            self.daemon_clean = finished
            if self.exit_code == 0 and self.runner.exit_code:
                self.exit_code = int(self.runner.exit_code)
            if finished:
                log.info("Daemon toza to'xtadi")
            else:
                log.warning("Daemon thread %.0f s ichida tugamadi — majburan chiqiladi", DAEMON_STOP_TIMEOUT_S)
            for stream in (sys.stdout, sys.stderr):
                with contextlib.suppress(Exception):
                    stream.flush()
            self._stop_run_loop()

        def _stop_run_loop(self) -> None:
            NSApp().stop_(None)
            # stop: keyingi hodisadan so'ng kuchga kiradi — bo'sh hodisa yuboramiz
            ev = NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
                NSEventTypeApplicationDefined, (0, 0), 0, 0, 0, None, 0, 0, 0
            )
            NSApp().postEvent_atStart_(ev, True)

        def _quit_now(self) -> None:
            self._begin_shutdown()


def run_desktop(settings: Settings, options: DesktopOptions | None = None, prefs_path: Path | None = None) -> int:
    """Desktop ilovani ishga tushiradi (asosiy thread'da bloklaydi). Qaytadi: chiqish kodi."""
    options = options or DesktopOptions()
    if not HAVE_COCOA:
        log.error("Desktop rejimi faqat macOS'da (pyobjc AppKit/WebKit kerak). `--headless` bilan ishga tushiring.")
        return 2
    if threading.current_thread() is not threading.main_thread():
        log.error("run_desktop() asosiy thread'da chaqirilishi shart")
        return 2

    prefs = DesktopPrefs(prefs_path)
    _set_process_display_name(APP_TITLE)
    app = NSApplication.sharedApplication()
    policy = NSApplicationActivationPolicyAccessory if options.hide_dock else NSApplicationActivationPolicyRegular
    app.setActivationPolicy_(policy)
    icon = _make_app_icon()
    if icon is not None:
        app.setApplicationIconImage_(icon)
    delegate = NexusDesktopApp.alloc().initWithSettings_options_prefs_(settings, options, prefs)
    app.setDelegate_(delegate)
    log.info(
        "Desktop rejimi: oyna=%s orb=%s dock=%s", options.window, options.orb, "yashirin" if options.hide_dock else "ha"
    )
    try:
        app.run()
    except KeyboardInterrupt:  # pragma: no cover
        delegate.daemon_clean = False  # signal MachSignals'dan o'tmagan — pastda majburan chiqiladi
    code = int(delegate.exit_code or 0)
    if not delegate.daemon_clean:
        # PortAudio/CoreAudio ichida osilib qolgan thread bo'lsa, atexit'dagi Pa_Terminate ham osiladi —
        # zombi jarayon qoldirmaslik uchun darhol chiqamiz.
        log.warning("Daemon toza tugamadi — jarayon majburan yakunlanmoqda (kod %d)", code)
        logging.shutdown()
        os._exit(code)
    return code
