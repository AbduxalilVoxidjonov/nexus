"""Nexus Ovoz OS — CLI kirish nuqtasi (`nexus` buyrug'i).

    nexus                    # desktop ilova: oyna + orb + menyu bar (daemon ichida)
    nexus --headless         # oynasiz, faqat daemon + web UI (http://127.0.0.1:8765)
    nexus --no-orb           # desktop, lekin orb overlay'siz
    nexus --no-window        # desktop, asosiy oynasiz (menyu bar + orb)
    nexus --no-ui            # faqat ovoz (UI serveri ham yo'q, headless)
    nexus --list-devices     # mikrofonlar ro'yxati
    nexus --check            # ruxsat va konfiguratsiya tekshiruvi
    nexus --text "Safari ni och"   # bir martalik matn buyrug'i (test)
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any

from nexus import __version__
from nexus.config import Settings, load_extra_env  # noqa: F401 — mos kelish uchun qayta eksport
from nexus.config import settings as global_settings
from nexus.events import EventBus
from nexus.events import bus as global_bus

log = logging.getLogger("nexus.main")

BANNER = r"""
  _   _                       ___
 | \ | | _____  ___   _ ___  / _ \__   _____ ____
 |  \| |/ _ \ \/ / | | / __|| | | \ \ / / _ \_  /
 | |\  |  __/>  <| |_| \__ \| |_| |\ V / (_) / /
 |_| \_|\___/_/\_\\__,_|___/ \___/  \_/ \___/___|   v{version}
"""


def platform_controller() -> Any:
    """Joriy OS uchun tizim kontrolleri (macOS — AppleScript, Windows — ctypes/PowerShell)."""
    if sys.platform == "win32":
        from nexus.windows_actions import WindowsController

        return WindowsController()
    from nexus.macos_actions import MacOSController

    return MacOSController()


# ---------------------------------------------------------------------------
# Metrikalar
# ---------------------------------------------------------------------------
class MetricsTicker:
    """Har `interval` sekundda cpu/ram/battery ni METRICS ga nashr qiladi."""

    def __init__(self, bus: EventBus, interval: float = 2.0, gemini: Any = None) -> None:
        self.bus = bus
        self.interval = interval
        self.gemini = gemini
        self._controller: Any = None
        self._started = time.monotonic()

    async def _info(self) -> dict[str, Any]:
        if self._controller is None:
            try:
                self._controller = platform_controller()
            except Exception as e:  # noqa: BLE001
                log.debug("MacOSController yo'q, psutil'ga o'tamiz: %s", e)
                self._controller = False
        if self._controller:
            try:
                info = await self._controller.get_system_info()
                if isinstance(info, dict):
                    return info
            except Exception as e:  # noqa: BLE001
                log.debug("get_system_info xatosi: %s", e)
        return self._psutil_info()

    @staticmethod
    def _psutil_info() -> dict[str, Any]:
        try:
            import psutil

            batt = psutil.sensors_battery()
            return {
                "cpu": float(psutil.cpu_percent(interval=None)),
                "ram": float(psutil.virtual_memory().percent),
                "battery": int(batt.percent) if batt else None,
            }
        except Exception:  # noqa: BLE001
            return {"cpu": 0.0, "ram": 0.0, "battery": None}

    def build_payload(self, info: dict[str, Any]) -> dict[str, Any]:
        """Nashr qilinadigan METRICS: snapshot'dagi eski maydonlar (reconnects, audio_dropped, ...)
        SAQLANADI, yangi qiymatlar ustun. UI har hodisada `S.metrics = d` qiladi — to'liq bo'lmasa
        ko'rsatkichlar "—" ga qaytib ketardi."""
        # get_system_info() *_percent kalitlarini, psutil zaxirasi qisqa kalitlarni qaytaradi
        fresh: dict[str, Any] = {
            "cpu": _first(info, "cpu", "cpu_percent"),
            "ram": _first(info, "ram", "ram_percent"),
            "battery": _first(info, "battery", "battery_percent"),
            "latency_ms": getattr(self.gemini, "last_latency_ms", None),
            "uptime_s": int(time.monotonic() - self._started),
        }
        for k, v in info.items():
            fresh.setdefault(k, v)
        if fresh["latency_ms"] is None:
            fresh.pop("latency_ms")  # snapshot'dagi oxirgi o'lchov qolsin
        data = dict(self.bus.snapshot.get("METRICS") or {})
        data.update(fresh)
        return data

    async def run(self) -> None:
        while True:
            info = await self._info()
            self.bus.publish("METRICS", self.build_payload(info))
            tick = getattr(self.gemini, "tick", None)
            if tick is not None:
                try:
                    tick()  # suhbat rejimi jimlik taymeri
                except Exception as e:  # noqa: BLE001
                    log.debug("gemini.tick xatosi: %s", e)
            await asyncio.sleep(self.interval)


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------
def _first(info: dict[str, Any], *keys: str) -> Any:
    """Berilgan kalitlardan birinchi None bo'lmagan qiymat."""
    for k in keys:
        v = info.get(k)
        if v is not None:
            return v
    return None


LOG_FILE = Path("~/.nexus/logs/nexus.log").expanduser()


def setup_logging(level: str, log_file: Path | None = LOG_FILE) -> None:
    """Konsol + aylanma log fayl (`~/.nexus/logs/nexus.log`, 2 MB × 3) — .app'da ham muammoni ko'rish uchun."""
    fmt = "%(asctime)s %(levelname)-5s %(name)s: %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file is not None:
        try:
            from logging.handlers import RotatingFileHandler

            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
            fh.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
            handlers.append(fh)
        except OSError as e:  # log fayl bo'lmasa ham ishlayveramiz
            print(f"Log fayl ochilmadi ({log_file}): {e}", file=sys.stderr)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    for noisy in ("websockets", "httpx", "httpcore", "uvicorn.access", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def print_banner(settings: Settings, device_name: str, ui: bool) -> None:
    print(BANNER.format(version=__version__))
    print(f"  Model     : {settings.gemini_model}  (ovoz: {settings.gemini_voice})")
    print(f"  Mikrofon  : {device_name}")
    if ui:
        print(f"  UI        : http://{settings.ui_host}:{settings.ui_port}")
    else:
        print("  UI        : o'chirilgan (--no-ui)")
    print("  Chiqish   : Ctrl+C\n", flush=True)  # log faylga yo'naltirilganda ham darhol ko'rinsin


async def check_environment(settings: Settings) -> int:
    """`--check`: konfiguratsiya, ruxsatlar va qurilmalarni tekshiradi. 0 = hammasi joyida."""
    from nexus.audio_streamer import list_input_devices

    problems = 0
    print("Nexus tekshiruvi\n" + "-" * 40)

    if settings.gemini_api_key.strip():
        print("[OK]  GEMINI_API_KEY topildi")
    else:
        print(
            "[XATO] GEMINI_API_KEY bo'sh yoki namunaviy (your_api_key_here) — ilovada Sozlamalar (⚙) → "
            "Gemini API kaliti orqali kiriting yoki .env fayliga yozing"
        )
        problems += 1
    print(f"[..]  Model: {settings.gemini_model}")

    try:
        import google.genai  # noqa: F401

        print("[OK]  google-genai SDK o'rnatilgan")
    except Exception as e:  # noqa: BLE001
        print(f"[XATO] google-genai import xatosi: {e}")
        problems += 1

    devs = list_input_devices()
    if devs:
        print(f"[OK]  Mikrofonlar: {len(devs)} ta")
        for d in devs:
            print(f"        {'*' if d['default'] else ' '} [{d['index']}] {d['name']}")
    else:
        print("[XATO] Mikrofon topilmadi yoki PortAudio yuklanmadi")
        problems += 1

    try:
        perms = await platform_controller().check_permissions()
        for k, v in (perms or {}).items():
            if not isinstance(v, (bool, type(None))):
                continue  # hints/message kabi qo'shimcha maydonlar
            mark = "OK" if v else ("??" if v is None else "!!")
            print(f"[{mark}]  Ruxsat: {k} = {'ha' if v else ('nomaʼlum' if v is None else 'YOʻQ')}")
            if v is False:
                problems += 1
        for h in perms.get("hints") or []:
            print(f"      → {h}")
    except Exception as e:  # noqa: BLE001
        print(f"[..]  Ruxsat tekshiruvi mavjud emas ({type(e).__name__}: {e})")

    print("-" * 40)
    print("Hammasi joyida." if problems == 0 else f"{problems} ta muammo topildi.")
    return 0 if problems == 0 else 1


def _register_state_commands(bus: EventBus, registry: Any) -> None:
    async def _get_state(_msg: dict) -> dict:
        return {"state": bus.state, "snapshot": bus.snapshot, "history": bus.history()}

    async def _run_tool(msg: dict) -> dict:
        name = str(msg.get("name", ""))
        args = dict(msg.get("args") or {})
        if registry is None:
            return {"ok": False, "error": "ToolRegistry mavjud emas"}
        before = bus.state
        result = await registry.execute(name, args)
        # UI dan qo'lda chaqirilgan tool (tasdiq rad etilgan bo'lsa ham) holatni
        # "processing"/"tool_executing" da qoldirmasin — Gemini navbati yo'q.
        if before in ("idle", "listening", "dictating") and bus.state in ("processing", "tool_executing"):
            bus.set_state(before)
        return {"result": result}

    bus.register_command("get_state", _get_state)
    bus.register_command("run_tool", _run_tool)


# ---------------------------------------------------------------------------
# Asosiy sikl
# ---------------------------------------------------------------------------
async def run(
    settings: Settings,
    *,
    ui: bool = True,
    one_shot_text: str | None = None,
    stop_event: asyncio.Event | None = None,
    install_signals: bool = True,
) -> int:
    """Daemon'ning asosiy sikli.

    `stop_event` — tashqaridan (masalan, desktop qatlamidan, `loop.call_soon_threadsafe(ev.set)`)
    to'xtatish uchun; berilmasa o'zi yaratadi. `install_signals=False` — SIGINT/SIGTERM
    handlerlari o'rnatilmaydi (asosiy bo'lmagan thread'da ishlaganda signal moduli ruxsat bermaydi;
    signalni GUI qatlami boshqaradi).
    """
    from nexus.audio_streamer import AudioStreamer
    from nexus.gemini_live_client import GeminiConfigError, GeminiLiveClient

    bus = global_bus
    bus.bind_loop()
    loop = asyncio.get_running_loop()
    if stop_event is None:
        stop_event = asyncio.Event()

    def _on_signal(sig: signal.Signals) -> None:
        log.info("Signal olindi: %s — to'xtatilmoqda", sig.name)
        stop_event.set()

    if install_signals:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _on_signal, sig)
            except (NotImplementedError, RuntimeError):  # pragma: no cover
                signal.signal(sig, lambda *_: stop_event.set())

    # Ruxsatlar (eslatma sifatida)
    try:
        perms = await platform_controller().check_permissions()
        log.info("Ruxsatlar: %s", perms)
        for k, v in (perms or {}).items():
            if v is False:
                bus.publish("LOG", {"level": "warn", "message": f"Ruxsat berilmagan: {k}"})
        for h in (perms or {}).get("hints") or []:
            bus.publish("LOG", {"level": "warn", "message": str(h)})
    except Exception as e:  # noqa: BLE001
        log.debug("check_permissions mavjud emas: %s", e)

    # Tool registry
    registry: Any = None
    try:
        from nexus.tools.registry import ToolRegistry

        registry = ToolRegistry(bus, settings)
    except Exception as e:  # noqa: BLE001
        log.error("ToolRegistry yuklanmadi (toolsiz rejim): %s", e)
    _register_state_commands(bus, registry)

    # Audio
    audio = AudioStreamer(bus, settings, loop=loop)
    audio.register_commands()
    audio.start()
    try:
        from nexus import video_translate

        video_translate.attach(bus, settings, audio)
    except Exception as e:  # noqa: BLE001
        log.debug("video_translate ulanmadi: %s", e)

    # UI
    ui_server: Any = None
    if ui and settings.serve_ui:
        try:
            from nexus.server import UIServer

            ui_server = UIServer(bus, settings)
            await ui_server.start()
        except Exception as e:  # noqa: BLE001
            log.error("UI serveri ishga tushmadi: %s", e)
            ui_server = None

    print_banner(settings, audio.current_device_name(), ui_server is not None)

    from nexus.config import save_api_key

    # UI bo'lsa kalit yo'qligi xato emas — Sozlamalardan kiritilguncha kutiladi (va `.env` ga saqlanadi)
    gemini = GeminiLiveClient(
        bus, settings, registry, audio, wait_for_key=ui_server is not None, key_saver=save_api_key
    )
    ticker = MetricsTicker(bus, interval=2.0, gemini=gemini)

    tasks: list[asyncio.Task] = [
        asyncio.create_task(ticker.run(), name="metrics"),
        asyncio.create_task(gemini.run(), name="gemini"),
    ]

    if one_shot_text:

        async def _one_shot() -> None:
            for _ in range(100):  # 10 s gacha ulanishni kutamiz
                if gemini.connected:
                    break
                await asyncio.sleep(0.1)
            await gemini.send_text(one_shot_text)

        tasks.append(asyncio.create_task(_one_shot(), name="one-shot"))

    exit_code = 0
    try:
        stop_wait = asyncio.create_task(stop_event.wait(), name="stop")
        done, _ = await asyncio.wait({stop_wait, tasks[1]}, return_when=asyncio.FIRST_COMPLETED)
        if tasks[1] in done and tasks[1].exception() is not None:
            exc = tasks[1].exception()
            if isinstance(exc, GeminiConfigError):
                print(f"\nXATO: {exc}\n", file=sys.stderr)
            else:
                log.error("Gemini mijozi xato bilan tugadi: %s", exc)
            exit_code = 2
        stop_wait.cancel()
    finally:
        log.info("To'xtatilmoqda...")
        await gemini.stop()
        try:
            from nexus import video_translate

            await video_translate.shutdown()
        except Exception as e:  # noqa: BLE001
            log.debug("video_translate shutdown xatosi: %s", e)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        audio.stop()
        if ui_server is not None:
            try:
                await ui_server.stop()
            except Exception as e:  # noqa: BLE001
                log.debug("UI stop xatosi: %s", e)
        log.info("Xayr.")
    return exit_code


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nexus", description="Nexus Ovoz OS — Gemini Live ovozli yordamchi")
    p.add_argument("--headless", action="store_true", help="Oynasiz: faqat daemon + web UI (eski rejim)")
    p.add_argument("--no-orb", action="store_true", help="Desktop rejimida orb overlay'ni ko'rsatmaslik")
    p.add_argument("--no-window", action="store_true", help="Desktop rejimida asosiy oynani ochmaslik")
    p.add_argument("--no-ui", action="store_true", help="Web UI serverini ishga tushirmaslik (headless)")
    p.add_argument("--no-playback", action="store_true", help="Javob ovozini ijro etmaslik")
    p.add_argument("--device", metavar="NAME", help="Mikrofon nomi yoki indeksi")
    p.add_argument("--list-devices", action="store_true", help="Mikrofonlar ro'yxatini chiqarish")
    p.add_argument("--check", action="store_true", help="Ruxsat va konfiguratsiyani tekshirish")
    p.add_argument("--text", metavar="MATN", help="Bir martalik matn buyrug'i (test uchun)")
    p.add_argument("--log-level", default=None, help="DEBUG/INFO/WARNING/ERROR")
    p.add_argument("--version", action="version", version=f"nexus {__version__}")
    return p


def desktop_mode(args: argparse.Namespace) -> bool:
    """Desktop (oyna + orb + menyu bar) rejimi kerakmi?

    `--headless`, `--no-ui` (server yo'q — oyna ko'rsatadigan narsa yo'q) va `--text`
    (bir martalik test buyrug'i) eski, oynasiz rejimni tanlaydi. macOS/Windows bo'lmasa ham headless.
    """
    if getattr(args, "headless", False) or getattr(args, "no_ui", False) or getattr(args, "text", None):
        return False
    return sys.platform in ("darwin", "win32")


def cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # `.env` manbalari `nexus.config` import vaqtida yuklangan; singleton'ni ishlatamiz —
    # web_answer / macos_actions ham aynan shu obyektni o'qiydi.
    settings = global_settings
    if args.log_level:
        settings.log_level = args.log_level
    if args.device:
        settings.input_device = args.device
    if args.no_playback:
        settings.playback_enabled = False
    setup_logging(settings.log_level)

    if args.list_devices:
        from nexus.audio_streamer import list_input_devices

        devs = list_input_devices()
        if not devs:
            print("Mikrofon topilmadi.")
            return 1
        for d in devs:
            print(f"{'*' if d['default'] else ' '} [{d['index']}] {d['name']}")
        return 0

    if args.check:
        return asyncio.run(check_environment(settings))

    if desktop_mode(args):
        from nexus.desktop import DesktopOptions

        if sys.platform == "win32":
            from nexus.desktop_win import run_desktop
        else:
            from nexus.desktop import run_desktop

        return run_desktop(settings, DesktopOptions.from_args(args))

    try:
        return asyncio.run(run(settings, ui=not args.no_ui, one_shot_text=args.text))
    except KeyboardInterrupt:  # pragma: no cover
        return 0


if __name__ == "__main__":
    sys.exit(cli())
