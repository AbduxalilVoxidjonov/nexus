"""UI ko'prigi: FastAPI + WebSocket server.

EventBus hodisalarini brauzerdagi UI ga uzatadi va UI dan kelgan
buyruqlarni `bus.dispatch_command` orqali daemon'ga yo'naltiradi.

Foydalanish (main.py):
    ui = UIServer(bus, settings)
    await ui.start()      # uvicorn fon taskda, bloklamaydi
    ...
    await ui.stop()

WS protokoli (`/ws`):
    server -> client:
        {"type": "HELLO", "ts": ..., "data": {"state": ..., "snapshot": {...}, "history": [...]}}
        {"type": "<EVENT>", "ts": ..., "data": {...}}            # EventBus hodisalari
        {"type": "CMD_RESULT", "ts": ..., "data": {...}, "reqId": ...}
    client -> server:
        {"cmd": "...", ..., "reqId": <ixtiyoriy>}
"""

from __future__ import annotations

import asyncio
import contextlib
import errno
import json
import logging
import socket
import time
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from nexus.config import Settings
from nexus.events import EventBus

log = logging.getLogger("nexus.server")

UI_DIR = Path(__file__).resolve().parent.parent / "ui"


def _snapshot(bus: EventBus, pending_confirm: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "state": bus.state,
        "snapshot": dict(bus.snapshot),
        "history": bus.history(),
        "pending_confirm": pending_confirm,
    }


class _ConfirmTracker:
    """CONFIRM_REQUEST / CONFIRM_RESOLVED hodisalarini kuzatib, ochiq tasdiqni eslab turadi.

    Shunda keyinroq ulangan UI ham HELLO orqali kutilayotgan tasdiqni ko'radi.
    """

    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.pending: dict[str, Any] | None = None
        self._task: asyncio.Task | None = None

    def ensure_started(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._watch(), name="nexus-confirm-tracker")

    def snapshot(self) -> dict[str, Any] | None:
        p = self.pending
        if p is None:
            return None
        ttl = p.get("ttl_s")
        if isinstance(ttl, (int, float)) and time.time() - p.get("ts", 0) > ttl:
            self.pending = None
            return None
        return p

    async def _watch(self) -> None:
        q = self.bus.subscribe()
        try:
            while True:
                ev = await q.get()
                data = ev.get("data") or {}
                if ev.get("type") == "CONFIRM_REQUEST":
                    self.pending = {**data, "ts": ev.get("ts", time.time())}
                elif ev.get("type") == "CONFIRM_RESOLVED" and (
                    self.pending is None or self.pending.get("token") == data.get("token")
                ):
                    self.pending = None
        finally:
            self.bus.unsubscribe(q)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._task
            self._task = None


def create_app(bus: EventBus, settings: Settings, ui_dir: Path | None = None) -> FastAPI:
    """FastAPI ilovasini yaratadi (testlarda ham shu ishlatiladi)."""
    ui_dir = ui_dir or UI_DIR
    app = FastAPI(title="Nexus Ovoz OS UI", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.bus = bus
    app.state.settings = settings
    app.state.clients = set()
    app.state.confirms = _ConfirmTracker(bus)

    def snapshot() -> dict[str, Any]:
        return _snapshot(bus, app.state.confirms.snapshot())

    if settings.serve_ui and ui_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")

    @app.middleware("http")
    async def no_cache(request: Any, call_next: Any) -> Any:
        # Desktop WKWebView (va brauzer) UI fayllarini eskirgan keshdan olmasin — har safar qayta tekshiradi
        response = await call_next(request)
        response.headers.setdefault("Cache-Control", "no-cache")
        return response

    @app.get("/")
    async def index() -> Any:
        if not settings.serve_ui:
            return JSONResponse({"ok": False, "error": "UI o'chirilgan (SERVE_UI=false)"}, status_code=404)
        index_file = ui_dir / "index.html"
        if not index_file.is_file():
            return JSONResponse({"ok": False, "error": "ui/index.html topilmadi"}, status_code=404)
        return FileResponse(str(index_file), media_type="text/html")

    @app.get("/orb")
    async def orb() -> Any:
        """Desktop orb overlay sahifasi (nexus/desktop.py shaffof NSPanel ichida yuklaydi)."""
        if not settings.serve_ui:
            return JSONResponse({"ok": False, "error": "UI o'chirilgan (SERVE_UI=false)"}, status_code=404)
        orb_file = ui_dir / "orb.html"
        if not orb_file.is_file():
            return JSONResponse({"ok": False, "error": "ui/orb.html topilmadi"}, status_code=404)
        return FileResponse(str(orb_file), media_type="text/html")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"ok": True, "state": bus.state}

    @app.get("/api/state")
    async def api_state() -> dict[str, Any]:
        return snapshot()

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        await ws.accept()
        app.state.confirms.ensure_started()
        app.state.clients.add(ws)
        queue = bus.subscribe()
        log.info("UI ulandi: %s (jami %d)", ws.client, len(app.state.clients))

        async def send(payload: dict[str, Any]) -> None:
            await ws.send_text(json.dumps(payload, ensure_ascii=False, default=str))

        async def sender() -> None:
            while True:
                event = await queue.get()
                await send(event)

        cmd_tasks: set[asyncio.Task] = set()

        async def handle_command(msg: dict[str, Any]) -> None:
            req_id = msg.get("reqId")
            try:
                result = await bus.dispatch_command(msg)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                result = {"ok": False, "cmd": msg.get("cmd"), "error": str(e)}
            if msg.get("cmd") == "get_state":
                # Handler bo'lmasa ham (yoki qisman javob bersa) bus snapshot'ini qo'shamiz
                if not result.get("ok"):
                    result = {"ok": True, "cmd": "get_state"}
                result = {**snapshot(), **result}
            with contextlib.suppress(Exception):
                await send(_cmd_result(result, req_id))

        async def receiver() -> None:
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await send(_cmd_result({"ok": False, "error": "JSON noto'g'ri"}, None))
                    continue
                if not isinstance(msg, dict):
                    await send(_cmd_result({"ok": False, "error": "Obyekt kutilgan edi"}, None))
                    continue
                # Buyruqlar parallel bajariladi: tasdiq kutayotgan run_tool shu soketdan
                # keladigan "confirm" buyrug'ini (va ping/pong'ni) to'sib qo'ymasligi kerak.
                task = asyncio.create_task(handle_command(msg))
                cmd_tasks.add(task)
                task.add_done_callback(cmd_tasks.discard)

        try:
            await send({"type": "HELLO", "ts": time.time(), "data": snapshot()})
            send_task = asyncio.create_task(sender())
            recv_task = asyncio.create_task(receiver())
            done, pending = await asyncio.wait({send_task, recv_task}, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await t
            for t in done:
                exc = t.exception()
                if exc is not None and not isinstance(exc, WebSocketDisconnect):
                    log.debug("WS oqimi xato bilan tugadi: %r", exc)
        except WebSocketDisconnect:
            pass
        except Exception as e:  # noqa: BLE001
            log.debug("WS sessiyasi uzildi: %r", e)
        finally:
            for t in list(cmd_tasks):
                t.cancel()
            bus.unsubscribe(queue)
            app.state.clients.discard(ws)
            log.info("UI uzildi: %s (qoldi %d)", ws.client, len(app.state.clients))

    return app


def _cmd_result(result: dict[str, Any], req_id: Any) -> dict[str, Any]:
    return {"type": "CMD_RESULT", "ts": time.time(), "data": result, "reqId": req_id}


class _QuietServer(uvicorn.Server):
    """Signal handlerlarini o'rnatmaydigan uvicorn Server (signalni main.py boshqaradi)."""

    @contextlib.contextmanager
    def capture_signals(self):  # type: ignore[override]
        yield

    def install_signal_handlers(self) -> None:  # eski uvicorn versiyalari uchun
        return None


class UIServer:
    """uvicorn'ni fon taskda ishga tushiradigan o'ram."""

    def __init__(self, bus: EventBus, settings: Settings) -> None:
        self.bus = bus
        self.settings = settings
        self.app = create_app(bus, settings)
        self._server: _QuietServer | None = None
        self._task: asyncio.Task | None = None
        self._sock: socket.socket | None = None

    @property
    def url(self) -> str:
        return f"http://{self.settings.ui_host}:{self.settings.ui_port}"

    def _bind(self) -> socket.socket:
        host, port = self.settings.ui_host, self.settings.ui_port
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            sock.listen(128)
        except OSError as e:
            sock.close()
            if e.errno in (errno.EADDRINUSE, errno.EACCES):
                log.error(
                    "UI porti band: %s:%d — boshqa Nexus nusxasi ishlayotgan bo'lishi mumkin. "
                    "UI_PORT ni o'zgartiring yoki eski jarayonni to'xtating (lsof -i :%d).",
                    host,
                    port,
                    port,
                )
            else:
                log.error("UI portini ochib bo'lmadi (%s:%d): %s", host, port, e)
            raise
        sock.set_inheritable(True)
        return sock

    async def start(self) -> None:
        if self._task is not None:
            return
        self._sock = self._bind()
        config = uvicorn.Config(
            self.app,
            host=self.settings.ui_host,
            port=self.settings.ui_port,
            log_level="warning",
            loop="asyncio",
            lifespan="off",
            access_log=False,
        )
        self._server = _QuietServer(config)
        self.app.state.confirms.ensure_started()
        self._task = asyncio.create_task(self._run(), name="nexus-ui-server")
        log.info(
            "UI ko'prigi ishga tushdi: %s (WS: ws://%s:%d/ws)",
            self.url,
            self.settings.ui_host,
            self.settings.ui_port,
        )

    async def _run(self) -> None:
        assert self._server is not None and self._sock is not None
        try:
            await self._server.serve(sockets=[self._sock])
        except SystemExit as e:
            log.error("uvicorn ishga tushmadi (kod %s).", e.code)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("UI serveri kutilmagan xato bilan to'xtadi")

    async def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except TimeoutError:
                log.warning("UI serveri 5 s ichida to'xtamadi, majburan bekor qilinmoqda")
                self._task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await self._task
            except asyncio.CancelledError:
                pass
        if self._sock is not None:
            with contextlib.suppress(OSError):
                self._sock.close()
        await self.app.state.confirms.stop()
        self._task = None
        self._server = None
        self._sock = None
        log.info("UI ko'prigi to'xtatildi")
