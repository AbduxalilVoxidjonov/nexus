"""Tool registry: Gemini function-call nomini handlerga yo'naltiradi, validatsiya, timeout, bekor qilish.

`execute` oqimi: loop guard → taint tekshiruvi → tasdiq kerakmi (statik REQUIRES_CONFIRMATION,
dinamik: terminal qo'riqchisi, sezgir/mavjud fayl, terminalga terish) → ConfirmationGate →
handler → (handler `needs_confirmation` qaytarsa → gate → qayta chaqirish) → taint belgilash.

`require_confirmation=False` (ilovadagi standart): foydalanuvchi buyrug'i tasdiqsiz bajariladi
(handlerga `confirmed=True` beriladi). Faqat taint sababi (shu navbatda tashqi matn o'qilgan —
prompt injection) bo'lsa — tasdiq sababi bor har qanday amal baribir so'raladi. `deny`
(taqiqlangan terminal buyruqlari) o'zgarmaydi.

`execute` natijasi: {"ok": bool, "output": str, "duration_ms": int, "error": str|None}
   (+ ixtiyoriy "note"/"next_step" — handler dict qaytarsa)

Kengaytma modullari (`EXTENSION_MODULES`) `TOOL_DECLARATIONS: list[dict]` va
`HANDLERS: dict[str, Callable[[dict], Awaitable[tuple[bool, str] | dict]]]` eksport qiladi;
yo'q bo'lsa jim o'tkaziladi.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import logging
import os
import sys
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from nexus.browser_actions import (
    BrowserController,
    BrowserDOMController,
    SearchInputController,
    SearchNavigationController,
    YouTubeController,
    normalize_browser,
    web_search,
)
from nexus.events import EventBus
from nexus.macos_actions import MacOSController
from nexus.safety import (
    DEFAULT_CONFIRM_TTL,
    INGESTS_EXTERNAL_CONTENT,
    ConfirmationGate,
    LoopGuard,
    TaintTracker,
    path_is_sensitive,
    redact_secrets,
)
from nexus.tools.schemas import ALL_TOOL_DECLARATIONS

log = logging.getLogger("nexus.tools")

DEFAULT_BROWSER = normalize_browser(os.getenv("DEFAULT_BROWSER", "chrome")) or "chrome"
TOOL_TIMEOUT = 30.0
MAX_OUTPUT = 4000

# Har doim tasdiq talab qiladigan toollar (qaytarib bo'lmaydigan amallar)
REQUIRES_CONFIRMATION = frozenset({"empty_trash", "delete_file", "sleep_display"})
# Ixtiyoriy kengaytma modullari: TOOL_DECLARATIONS + HANDLERS eksport qiladi
EXTENSION_MODULES: list[str] = [
    "nexus.file_actions",
    "nexus.ax_actions",
    "nexus.web_answer",
    "nexus.screen_reader",
    "nexus.video_translate",
]
IS_WINDOWS = sys.platform == "win32"
# Enter bosilganda terminaldagi qatorni bajaradigan klavishlar
_ENTER_KEYS = frozenset({"enter", "return"})

Handler = Callable[[dict[str, Any]], Awaitable[tuple[bool, Any] | dict[str, Any]]]


def _truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n… [{len(text) - limit} belgi qisqartirildi]"


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "summary" in value:
        return str(value["summary"])
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


class ToolRegistry:
    """Gemini toollarini bajaruvchi markaziy ro'yxat."""

    def __init__(self, bus: EventBus | None = None, settings: Any = None) -> None:
        self.bus = bus
        self.settings = settings
        if IS_WINDOWS:
            from nexus.windows_actions import WindowsController
            from nexus.windows_browser import WindowsBrowser

            self.mac = WindowsController()
            # bitta obyekt macOS'dagi beshta brauzer sinfining API'sini beradi
            self.tabs = self.dom = self.youtube = self.search = self.search_input = WindowsBrowser()
        else:
            self.mac = MacOSController()
            self.tabs = BrowserController()
            self.dom = BrowserDOMController()
            self.youtube = YouTubeController(self.dom)
            self.search = SearchNavigationController(self.dom, self.tabs)
            self.search_input = SearchInputController(self.dom)
        self.confirm_ttl = float(
            getattr(settings, "confirm_ttl_s", DEFAULT_CONFIRM_TTL) or DEFAULT_CONFIRM_TTL
        )
        self.gate = ConfirmationGate(bus, ttl_s=self.confirm_ttl)
        # settings berilmasa (testlar, eski chaqiruvlar) — xavfsiz standart: tasdiq so'raladi
        self.require_confirmation: bool = (
            True if settings is None else bool(getattr(settings, "require_confirmation", True))
        )
        self.taint = TaintTracker()
        self.loop_guard = LoopGuard()
        self._running: set[asyncio.Task] = set()
        # `kill_all` ilgagi: Gemini klienti o'z tool tasklarini bekor qilish / player'ni tozalash
        # uchun o'rnatadi (sync yoki async). Klient `kill_all` buyrug'ini o'zi ro'yxatdan o'tkazMAYDI —
        # aks holda registry'ning gate.cancel_pending() chaqiruvi ustidan yozilib qolardi.
        self.on_kill_all: Callable[[], Any] | None = None
        self._decls: dict[str, dict] = {d["name"]: d for d in ALL_TOOL_DECLARATIONS}
        self._handlers: dict[str, Handler] = self._build_handlers()
        if IS_WINDOWS:
            # Windows ekvivalenti hali yo'q toollar Gemini'ga e'lon qilinmaydi
            from nexus.windows_actions import SUPPORTED_TOOLS

            self._decls = {k: v for k, v in self._decls.items() if k in SUPPORTED_TOOLS}
        self.extensions: list[str] = []
        self._load_extensions()
        if IS_WINDOWS:
            from nexus.windows_actions import adapt_declaration

            self._decls = {k: adapt_declaration(v) for k, v in self._decls.items()}

        missing = set(self._decls) - set(self._handlers)
        if missing:
            raise RuntimeError(f"Handler yo'q toollar: {sorted(missing)}")

        if bus is not None:
            bus.register_command("run_tool", self._cmd_run_tool)
            bus.register_command("kill_all", self._cmd_kill_all)
            bus.register_command("new_turn", self._cmd_new_turn)
            bus.register_command("utterance", self._cmd_utterance)
            bus.register_command("confirmations", self._cmd_confirmations)
            self.publish_settings()

    # ------------------------------------------------------------------
    # Kengaytma modullari
    # ------------------------------------------------------------------
    def _load_extensions(self) -> None:
        modules: list[str] | tuple[str, ...] = EXTENSION_MODULES
        if IS_WINDOWS:
            from nexus.windows_actions import WINDOWS_EXTENSION_MODULES

            modules = WINDOWS_EXTENSION_MODULES
        for mod_name in modules:
            try:
                mod = importlib.import_module(mod_name)
            except ImportError as e:
                log.info("Kengaytma moduli yo'q, o'tkazildi: %s (%s)", mod_name, e)
                continue
            except Exception:
                log.exception("Kengaytma moduli yuklanmadi: %s", mod_name)
                continue
            decls = getattr(mod, "TOOL_DECLARATIONS", None) or []
            handlers = getattr(mod, "HANDLERS", None) or {}
            added = 0
            for d in decls:
                name = d.get("name") if isinstance(d, dict) else None
                if not name:
                    continue
                handler = handlers.get(name)
                if handler is None:
                    log.warning("%s: '%s' deklaratsiyasi uchun handler yo'q — o'tkazildi", mod_name, name)
                    continue
                if name in self._decls:
                    log.warning("%s: '%s' allaqachon mavjud — o'tkazildi", mod_name, name)
                    continue
                self._decls[name] = d
                self._handlers[name] = self._wrap_ext_handler(handler)
                added += 1
            self.extensions.append(mod_name)
            log.info("Kengaytma yuklandi: %s (%d ta tool)", mod_name, added)

    @staticmethod
    def _wrap_ext_handler(handler: Callable[..., Any]) -> Handler:
        async def run(args: dict[str, Any]) -> Any:
            res = handler(args)
            if inspect.isawaitable(res):
                res = await res
            return res

        return run

    # ------------------------------------------------------------------
    # Ochiq API
    # ------------------------------------------------------------------
    def declarations(self) -> list[dict]:
        return list(self._decls.values())

    def has(self, name: str) -> bool:
        return name in self._handlers

    def new_turn(self) -> None:
        """Foydalanuvchi yangi gap boshladi: loop guard va taint tozalanadi."""
        self.loop_guard.new_turn()
        self.taint.new_turn()

    def note_utterance(self, text: str, ts: float | None = None) -> bool | None:
        """Foydalanuvchining yakuniy transkripti — og'zaki tasdiq uchun."""
        return self.gate.note_utterance(text, ts)

    @property
    def running(self) -> int:
        return len([t for t in self._running if not t.done()])

    def cancel_all(self) -> int:
        """Bajarilayotgan tool tasklarini bekor qiladi.

        Kutilayotgan tasdiq so'roviga TEGMAYDI: gemini client buni barge-in (`interrupted`) da
        chaqiradi, foydalanuvchining "ha" deyishi esa aynan shunday barge-in. Tasdiqni faqat
        aniq `kill_all` buyrug'i bekor qiladi.
        """
        n = 0
        for task in list(self._running):
            if not task.done():
                task.cancel()
                n += 1
        return n

    async def kill_all(self) -> int:
        """⌥⎋ / "kill_all": tool tasklar + kutilayotgan tasdiq bekor qilinadi, so'ng `on_kill_all` ilgagi.

        Qaytaradi: bekor qilingan elementlar soni (tasdiq so'rovi ham 1 deb hisoblanadi).
        """
        n = self.cancel_all()
        if self.gate.cancel_pending("cancelled"):
            n += 1
        hook = self.on_kill_all
        if hook is not None:
            try:
                res = hook()
                if inspect.isawaitable(res):
                    await res
            except Exception as e:  # noqa: BLE001
                log.warning("on_kill_all ilgagi xatosi: %s", e)
        return n

    async def execute(self, name: str, args: dict | None = None) -> dict[str, Any]:
        start = time.monotonic()
        args = dict(args or {})
        result = await self._execute_inner(name, args)
        result["duration_ms"] = int((time.monotonic() - start) * 1000)
        result["output"] = _truncate(result.get("output") or "")
        if self.bus is not None:
            try:
                self.bus.publish(
                    "TOOL_CALLED",
                    {
                        "name": name,
                        "args": args,
                        "duration_ms": result["duration_ms"],
                        "ok": result["ok"],
                        "output": result["output"],
                    },
                )
            except Exception:
                log.exception("TOOL_CALLED nashr qilinmadi")
        log.info("tool %s ok=%s %dms", name, result["ok"], result["duration_ms"])
        return result

    async def _execute_inner(self, name: str, args: dict) -> dict[str, Any]:
        decl = self._decls.get(name)
        handler = self._handlers.get(name)
        if decl is None or handler is None:
            return {"ok": False, "output": "", "error": f"Noma'lum tool: {name}"}

        ok, err, clean = self._validate(decl, args)
        if not ok:
            return {"ok": False, "output": "", "error": f"Argument xatosi ({name}): {err}"}

        looping = self.loop_guard.check(name, clean)
        if looping is not None:
            return {"ok": False, "output": "", "error": looping}

        # Tasdiq o'chiq bo'lsa ham: shu navbatda tashqi matn o'qilgan bo'lsa (prompt injection ehtimoli)
        # odatda tasdiq talab qiladigan har qanday amal (savat, o'chirish, terminal...) so'raladi
        tainted = self.taint.tainted
        reasons = await self._confirmation_reasons(name, clean)
        if reasons:
            if self.require_confirmation or tainted:
                approved = await self._ask(name, clean, reasons)
                if not approved:
                    return self._not_confirmed(name)
            else:
                log.info("Tasdiqsiz bajarilmoqda (%s): %s", name, "; ".join(reasons))
            clean["confirmed"] = True

        result = await self._run_handler(name, handler, clean)

        if result.get("needs_confirmation") and not clean.get("confirmed"):
            summary = str(result.get("summary") or result.get("output") or name)
            if self.require_confirmation or tainted:
                approved = await self._ask(name, clean, [summary], summary=summary)
                if not approved:
                    return self._not_confirmed(name)
            else:
                log.info("Tasdiqsiz bajarilmoqda (%s): %s", name, summary)
            clean["confirmed"] = True
            result = await self._run_handler(name, handler, clean)

        if name in INGESTS_EXTERNAL_CONTENT:
            result["output"] = redact_secrets(result.get("output") or "")
        self.taint.after(name)
        return result

    async def _run_handler(self, name: str, handler: Handler, clean: dict) -> dict[str, Any]:
        task = asyncio.create_task(handler(dict(clean)), name=f"tool:{name}")
        self._running.add(task)
        task.add_done_callback(self._running.discard)
        try:
            raw = await asyncio.wait_for(task, timeout=TOOL_TIMEOUT)
        except TimeoutError:
            return {"ok": False, "output": "", "error": f"{name}: vaqt tugadi ({TOOL_TIMEOUT:.0f}s)"}
        except asyncio.CancelledError:
            current = asyncio.current_task()
            if task.cancelled() and not (current is not None and current.cancelling()):
                return {"ok": False, "output": "", "error": f"{name}: bekor qilindi"}
            raise
        except Exception as e:
            log.exception("Tool ichki xatosi: %s", name)
            return {"ok": False, "output": "", "error": f"{name}: {type(e).__name__}: {e}"}
        return self._normalize(name, raw)

    @staticmethod
    def _normalize(name: str, raw: Any) -> dict[str, Any]:
        """Handler javobini (tuple yoki dict) yagona formatga keltiradi."""
        if isinstance(raw, dict):
            res: dict[str, Any] = {"ok": bool(raw.get("ok", not raw.get("error")))}
            if raw.get("needs_confirmation"):
                res["needs_confirmation"] = True
                res["summary"] = str(raw.get("summary") or raw.get("action") or name)
                res["ok"] = False
            out = raw.get("output")
            if out is None:
                out = raw.get("summary") if "summary" in raw else raw.get("message")
            if out is None:
                body = {k: v for k, v in raw.items() if k not in {"ok", "error", "note", "next_step"}}
                out = _to_text(body) if body else ""
            text = _to_text(out)
            res["output"] = text
            res["error"] = str(raw["error"]) if raw.get("error") else (None if res["ok"] else text or None)
            for extra in ("note", "next_step"):
                if raw.get(extra):
                    res[extra] = str(raw[extra])
                    res["output"] = (res["output"] + f"\n[{extra}] {raw[extra]}").strip()
            return res
        try:
            h_ok, h_out = raw
        except (TypeError, ValueError):
            return {"ok": False, "output": "", "error": f"{name}: handler noto'g'ri javob qaytardi"}
        text = _to_text(h_out)
        if h_ok:
            return {"ok": True, "output": text, "error": None}
        return {"ok": False, "output": text, "error": text or f"{name}: bajarilmadi"}

    # ------------------------------------------------------------------
    # Tasdiq
    # ------------------------------------------------------------------
    async def _confirmation_reasons(self, name: str, args: dict) -> list[str]:
        """Bajarishdan OLDIN aniqlanadigan tasdiq sabablari (bo'sh — tasdiqsiz)."""
        reasons: list[str] = []
        if self.taint.requires_confirmation(name):
            reasons.append(self.taint.reason(name))
        if name in REQUIRES_CONFIRMATION:
            reasons.append(f"{name} — qaytarib bo'lmaydigan amal")
        if name == "run_terminal_command":
            verdict, why = self.mac.guard.check(str(args.get("command") or ""))
            if verdict == "confirm":
                reasons.append(f"terminal: {why}")
        elif name == "write_file":
            path = args.get("path") or args.get("file") or ""
            if path:
                if path_is_sensitive(path):
                    reasons.append(f"sezgir yo'l: {path}")
                else:
                    try:
                        exists = Path(str(path)).expanduser().exists()
                    except OSError:
                        exists = False
                    appending = bool(args.get("append")) or str(args.get("mode") or "").lower() == "append"
                    if exists and not appending:
                        reasons.append(f"mavjud fayl ustiga yozish: {path}")
        elif name == "type_text":
            if await self.mac.is_terminal_frontmost():
                reasons.append("terminal old oynada — terilgan matn buyruq sifatida bajariladi")
        elif name == "press_hotkey":
            keys = {k.strip().lower() for k in str(args.get("keys") or "").replace("-", "+").split("+")}
            if keys & _ENTER_KEYS and await self.mac.is_terminal_frontmost():
                reasons.append("terminalda Enter — joriy qator bajariladi")
        return reasons

    def set_require_confirmation(self, value: bool) -> bool:
        self.require_confirmation = bool(value)
        if self.settings is not None:
            try:
                self.settings.require_confirmation = self.require_confirmation
            except AttributeError:
                pass
        self.publish_settings()
        return self.require_confirmation

    def publish_settings(self) -> None:
        if self.bus is None:
            return
        data = dict(self.bus.snapshot.get("SETTINGS") or {})
        data["require_confirmation"] = self.require_confirmation
        self.bus.publish("SETTINGS", data)

    async def _cmd_confirmations(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"require_confirmation": self.set_require_confirmation(bool(msg.get("value", True)))}

    async def _ask(self, name: str, args: dict, reasons: list[str], summary: str | None = None) -> bool:
        summary = summary or self._summarize(name, args)
        token = self.gate.request(name, summary, "; ".join(reasons), ttl_s=self.confirm_ttl)
        if self.bus is not None:
            # info: UI CONFIRM_REQUEST uchun o'zi toast ko'rsatadi — ikkilangan ogohlantirish bo'lmasin
            self.bus.publish("LOG", {"level": "info", "message": f"Tasdiq kutilmoqda: {summary}"})
        return await self.gate.wait(token, self.confirm_ttl)

    @staticmethod
    def _summarize(name: str, args: dict) -> str:
        shown = {k: v for k, v in args.items() if k not in {"confirmed", "browser"}}
        if name == "run_terminal_command":
            return f"Terminal: {args.get('command', '')}"
        if name == "type_text":
            t = str(args.get("text", ""))
            return f"Terish: {t[:60]}{'…' if len(t) > 60 else ''}"
        if not shown:
            return name
        body = json.dumps(shown, ensure_ascii=False, default=str)
        return f"{name} {body[:120]}"

    @staticmethod
    def _not_confirmed(name: str) -> dict[str, Any]:
        return {
            "ok": False,
            "output": "Foydalanuvchi tasdiqlamadi",
            "error": f"{name}: foydalanuvchi tasdiqlamadi (rad etildi yoki vaqt tugadi) — amal bajarilmadi",
        }

    # ------------------------------------------------------------------
    # Validatsiya
    # ------------------------------------------------------------------
    @staticmethod
    def _validate(decl: dict, args: dict) -> tuple[bool, str, dict]:
        params = decl.get("parameters") or {}
        props: dict[str, dict] = params.get("properties") or {}
        required: list[str] = params.get("required") or []
        clean: dict[str, Any] = {}

        for key in required:
            if args.get(key) is None or (isinstance(args.get(key), str) and not args[key].strip()):
                return False, f"'{key}' majburiy", {}

        for key, value in args.items():
            spec = props.get(key)
            if spec is None:
                continue  # noma'lum argumentlar e'tiborsiz qoldiriladi
            if value is None:
                continue
            t = spec.get("type")
            try:
                if t == "INTEGER":
                    value = int(float(value)) if not isinstance(value, bool) else int(value)
                elif t == "NUMBER":
                    value = float(value)
                elif t == "BOOLEAN":
                    if isinstance(value, str):
                        value = value.strip().lower() in {"1", "true", "yes", "ha", "on", "да"}
                    else:
                        value = bool(value)
                elif t == "STRING":
                    value = str(value)
            except (TypeError, ValueError):
                return False, f"'{key}' turi noto'g'ri ({t} kutilgan)", {}
            enum = spec.get("enum")
            if enum and isinstance(value, str):
                low = value.strip().lower()
                match = next((e for e in enum if e.lower() == low), None)
                if match is None:
                    if key == "browser":
                        match = normalize_browser(value)
                    if match is None:
                        return False, f"'{key}' qiymati {enum} ichidan bo'lishi kerak", {}
                value = match
            clean[key] = value
        return True, "", clean

    # ------------------------------------------------------------------
    # Bus buyruqlari
    # ------------------------------------------------------------------
    async def _cmd_run_tool(self, msg: dict) -> dict:
        name = str(msg.get("name") or "")
        args = msg.get("args") or {}
        if not isinstance(args, dict):
            return {
                "result": {"ok": False, "output": "", "error": "args lug'at bo'lishi kerak", "duration_ms": 0}
            }
        return {"result": await self.execute(name, args)}

    async def _cmd_kill_all(self, msg: dict) -> dict:
        n = await self.kill_all()
        if self.bus is not None:
            self.bus.publish("LOG", {"level": "warn", "message": f"{n} ta tool bekor qilindi"})
        return {"cancelled": n}

    async def _cmd_new_turn(self, msg: dict) -> dict:
        self.new_turn()
        return {}

    async def _cmd_utterance(self, msg: dict) -> dict:
        text = str(msg.get("value") or msg.get("text") or "")
        ts = msg.get("ts")
        verdict = self.note_utterance(text, float(ts) if ts is not None else None)
        return {"verdict": verdict}

    # ------------------------------------------------------------------
    # Handlerlar
    # ------------------------------------------------------------------
    def _browser(self, args: dict) -> str:
        if IS_WINDOWS:  # chrome/edge/firefox — WindowsBrowser o'zi tanlaydi (bo'sh — istalgan brauzer)
            return str(args.get("browser") or "")
        return normalize_browser(args.get("browser")) or DEFAULT_BROWSER

    def _build_handlers(self) -> dict[str, Handler]:
        m = self.mac

        async def launch_app(a: dict):
            return await m.launch_app(a["name"])

        async def list_applications(a: dict):
            return await m.list_applications(a.get("filter"))

        async def quit_app(a: dict):
            return await m.quit_app(a["name"])

        async def set_volume(a: dict):
            return await m.set_volume(a["level"])

        async def mute_volume(a: dict):
            return await m.mute_volume(bool(a.get("mute", True)))

        async def volume_step(a: dict):
            return await m.volume_step(a["delta"])

        async def control_media(a: dict):
            return await m.media_control(a["action"])

        async def now_playing(a: dict):
            return await m.now_playing()

        async def set_brightness(a: dict):
            return await m.set_brightness_keys(a["direction"] == "increase", int(a.get("steps") or 2))

        async def run_terminal_command(a: dict):
            return await m.run_terminal_command(a["command"], confirmed=bool(a.get("confirmed")))

        async def take_screenshot(a: dict):
            return await m.take_screenshot(a.get("target_path") or None)

        async def get_system_info(a: dict):
            return True, await m.get_system_info()

        async def open_folder(a: dict):
            return await m.open_folder(a["path"])

        async def open_path(a: dict):
            return await m.open_path(a["path"])

        async def send_notification(a: dict):
            return await m.send_notification(a["title"], a["message"])

        async def lock_screen(a: dict):
            return await m.lock_screen()

        async def sleep_display(a: dict):
            return await m.sleep_display()

        async def toggle_dark_mode(a: dict):
            return await m.toggle_dark_mode()

        async def set_do_not_disturb(a: dict):
            return await m.set_do_not_disturb(bool(a.get("on", True)))

        async def get_clipboard(a: dict):
            return await m.get_clipboard()

        async def set_clipboard(a: dict):
            return await m.set_clipboard(a["text"])

        async def type_text(a: dict):
            return await m.type_text(a["text"], press_enter=bool(a.get("press_enter", False)))

        async def press_hotkey(a: dict):
            return await m.press_hotkey(a["keys"])

        async def list_running_apps(a: dict):
            return await m.list_running_apps()

        async def hide_all_windows(a: dict):
            return await m.hide_all_windows()

        async def empty_trash(a: dict):
            return await m.empty_trash()

        async def say_text(a: dict):
            return await m.say_text(a["text"])

        async def _dictation(on: bool):
            if self.bus is None:
                return False, "Diktovka moduli ulanmagan (event bus yo'q)"
            res = await self.bus.dispatch_command({"cmd": "dictation", "value": on})
            if not res.get("ok"):
                err = res.get("error") or "noma'lum xato"
                return False, f"Diktovka rejimi mavjud emas: {err}"
            return True, "Diktovka boshlandi — aytilganlar teriladi" if on else "Diktovka to'xtatildi"

        async def start_dictation(a: dict):
            return await _dictation(True)

        async def stop_dictation(a: dict):
            return await _dictation(False)

        async def _conversation(on: bool):
            if self.bus is None:
                return False, "Suhbat rejimi ulanmagan (event bus yo'q)"
            res = await self.bus.dispatch_command({"cmd": "conversation", "value": on})
            if not res.get("ok"):
                err = res.get("error") or "noma'lum xato"
                return False, f"Suhbat rejimi mavjud emas: {err}"
            if on:
                return True, (
                    "Suhbat rejimi yoqildi: endi foydalanuvchining hamma gapi senga qaratilgan, ism shart emas. "
                    "Erkin suhbatlash, ma'nosini tushunib javob ber."
                )
            return True, "Suhbat rejimi tugadi: endi faqat ism bilan chaqirilganda javob berasan."

        async def start_conversation(a: dict):
            return await _conversation(True)

        async def stop_conversation(a: dict):
            return await _conversation(False)

        # -- brauzer --
        async def browser_open_url(a: dict):
            return await self.tabs.open_url(self._browser(a), a["url"])

        async def browser_switch_tab(a: dict):
            return await self.tabs.switch_to_tab(self._browser(a), a["keyword"])

        async def browser_close_tab(a: dict):
            return await self.tabs.close_current_tab(self._browser(a))

        async def browser_reload(a: dict):
            return await self.tabs.reload(self._browser(a))

        async def browser_current_page(a: dict):
            return await self.tabs.current_page(self._browser(a))

        async def browser_list_tabs(a: dict):
            return await self.tabs.list_tabs(self._browser(a))

        async def browser_scroll(a: dict):
            return await self.dom.scroll_page(self._browser(a), a["direction"], int(a.get("amount") or 600))

        async def browser_click_button(a: dict):
            return await self.dom.click_by_text(self._browser(a), a["button_text"])

        async def browser_click_selector(a: dict):
            return await self.dom.click_element(self._browser(a), a["selector"])

        async def browser_read_page(a: dict):
            return await self.dom.get_page_text_summary(self._browser(a), int(a.get("max_chars") or 1500))

        async def browser_type_and_search(a: dict):
            return await self.search_input.type_query_and_search(
                self._browser(a), a["query"], bool(a.get("auto_submit", True))
            )

        async def web_search_h(a: dict):
            return await web_search(self._browser(a), a["query"], a.get("engine") or "google", tabs=self.tabs)

        async def search_get_results(a: dict):
            return await self.search.get_results_text(self._browser(a), int(a.get("limit") or 10))

        async def search_open_result(a: dict):
            b = self._browser(a)
            new_tab = bool(a.get("new_tab", False))
            if a.get("index") is not None:
                return await self.search.open_result_by_index(b, int(a["index"]), new_tab)
            if a.get("keyword"):
                return await self.search.open_result_by_match(b, a["keyword"], new_tab)
            return False, "index yoki keyword ko'rsatilishi kerak"

        async def search_navigate_page(a: dict):
            return await self.search.navigate_page(self._browser(a), a["direction"])

        async def youtube_control(a: dict):
            b = self._browser(a)
            yt = self.youtube
            action = a["action"]
            if action == "toggle_play":
                return await yt.toggle_play(b)
            if action == "play":
                return await yt.play(b)
            if action == "pause":
                return await yt.pause(b)
            if action == "seek":
                return await yt.seek(b, a.get("seek_seconds") if a.get("seek_seconds") is not None else 10)
            if action == "seek_to":
                return await yt.seek_to(b, a.get("seek_seconds") or 0)
            if action == "restart":
                return await yt.restart(b)
            if action == "set_volume":
                if a.get("volume") is None:
                    return False, "volume parametri kerak (0-100)"
                return await yt.set_player_volume(b, a["volume"])
            if action == "toggle_mute":
                return await yt.toggle_mute(b)
            if action == "set_speed":
                return await yt.set_playback_rate(b, a.get("speed") or 1.0)
            if action == "toggle_fullscreen":
                return await yt.toggle_fullscreen(b)
            if action == "toggle_subtitles":
                return await yt.toggle_subtitles(b)
            if action == "next_video":
                return await yt.next_video(b)
            if action == "get_info":
                return await yt.get_video_info(b)
            return False, f"Noma'lum YouTube amali: {action}"

        return {
            "launch_app": launch_app,
            "list_applications": list_applications,
            "quit_app": quit_app,
            "set_volume": set_volume,
            "mute_volume": mute_volume,
            "volume_step": volume_step,
            "control_media": control_media,
            "now_playing": now_playing,
            "set_brightness": set_brightness,
            "run_terminal_command": run_terminal_command,
            "take_screenshot": take_screenshot,
            "get_system_info": get_system_info,
            "open_folder": open_folder,
            "open_path": open_path,
            "send_notification": send_notification,
            "lock_screen": lock_screen,
            "sleep_display": sleep_display,
            "toggle_dark_mode": toggle_dark_mode,
            "set_do_not_disturb": set_do_not_disturb,
            "get_clipboard": get_clipboard,
            "set_clipboard": set_clipboard,
            "type_text": type_text,
            "press_hotkey": press_hotkey,
            "list_running_apps": list_running_apps,
            "hide_all_windows": hide_all_windows,
            "empty_trash": empty_trash,
            "say_text": say_text,
            "start_dictation": start_dictation,
            "stop_dictation": stop_dictation,
            "start_conversation": start_conversation,
            "stop_conversation": stop_conversation,
            "browser_open_url": browser_open_url,
            "browser_switch_tab": browser_switch_tab,
            "browser_close_tab": browser_close_tab,
            "browser_reload": browser_reload,
            "browser_current_page": browser_current_page,
            "browser_list_tabs": browser_list_tabs,
            "browser_scroll": browser_scroll,
            "browser_click_button": browser_click_button,
            "browser_click_selector": browser_click_selector,
            "browser_read_page": browser_read_page,
            "browser_type_and_search": browser_type_and_search,
            "web_search": web_search_h,
            "search_get_results": search_get_results,
            "search_open_result": search_open_result,
            "search_navigate_page": search_navigate_page,
            "youtube_control": youtube_control,
        }


__all__ = ["DEFAULT_BROWSER", "EXTENSION_MODULES", "REQUIRES_CONFIRMATION", "TOOL_TIMEOUT", "ToolRegistry"]
