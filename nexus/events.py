"""Daemon ichidagi hodisalar shinasi (event bus).

Barcha modullar (audio, gemini, tools) hodisalarni shu yerga `publish` qiladi;
`server.py` esa ularni WebSocket orqali UI ga tarqatadi. UI dan kelgan
buyruqlar (`cmd`) esa `dispatch_command` orqali ro'yxatdan o'tgan
handlerlarga yo'naltiriladi.

Hodisa formati (JSON):
    {"type": "<TYPE>", "ts": <unix float>, "data": {...}}

Turlar:
    STATE_CHANGE  data={"state": "idle|listening|processing|tool_executing|speaking"}
    TRANSCRIPT    data={"role": "user|assistant", "text": str, "final": bool}
    TOOL_CALLED   data={"name": str, "args": dict, "duration_ms": int, "ok": bool, "output": str}
    AUDIO_LEVEL   data={"rms": float(0..1), "db": float(-60..0)}
    METRICS       data={"cpu": float, "ram": float, "battery": int|None, "latency_ms": int|None, ...}
    CONNECTION    data={"gemini": "connected|reconnecting|disconnected", "attempt": int, "detail": str}
    LOG           data={"level": "info|warn|error", "message": str}
    DEVICES       data={"devices": [{"index": int, "name": str, "default": bool}], "current": int|None}
    SETTINGS      data={"muted": bool, "ptt": bool, "sensitivity": float, "playback": bool,
                        "wake_mode": "always|name|smart", "name": str, "dictating": bool}
    CONFIRM_REQUEST data={"token": str, "action": str, "summary": str, "reason": str, "ttl_s": int}
                  # xavfli amal tasdiq kutmoqda (og'zaki "ha" yoki UI tugmasi)
    CONFIRM_RESOLVED data={"token": str, "approved": bool, "source": "voice|ui|timeout|cancelled"}

UI -> daemon buyruqlari (JSON):
    {"cmd": "mute", "value": bool}
    {"cmd": "ptt", "value": bool}            # push-to-talk rejimi yoqilgan/o'chgan
    {"cmd": "ptt_press", "value": bool}      # PTT tugmasi bosilgan/qo'yib yuborilgan
    {"cmd": "sensitivity", "value": float}   # 0..1
    {"cmd": "set_device", "index": int}
    {"cmd": "list_devices"}
    {"cmd": "kill_all"}                      # barcha bajarilayotgan toollarni to'xtatish
    {"cmd": "get_state"}                     # to'liq snapshot qaytaradi
    {"cmd": "text", "value": str}            # matnli xabar yuborish (mikrofonsiz)
    {"cmd": "run_tool", "name": str, "args": dict}  # UI dan bevosita tool chaqirish
    {"cmd": "confirm", "token": str, "approve": bool}   # CONFIRM_REQUEST ga javob
    {"cmd": "wake_mode", "value": "always|name|smart"}
    {"cmd": "set_name", "value": str}
    {"cmd": "dictation", "value": bool}
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any

log = logging.getLogger("nexus.events")

CommandHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any] | None]]

STATES = ("idle", "listening", "processing", "tool_executing", "speaking", "dictating", "awaiting_confirmation")


class EventBus:
    """Thread-safe pub/sub. `publish` istalgan thread'dan chaqirilishi mumkin."""

    def __init__(self, history: int = 200) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._subscribers: set[asyncio.Queue] = set()
        self._handlers: dict[str, CommandHandler] = {}
        self._history: deque[dict[str, Any]] = deque(maxlen=history)
        self.state: str = "idle"
        self.snapshot: dict[str, Any] = {}

    # --- hayot sikli -------------------------------------------------
    def bind_loop(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self._loop = loop or asyncio.get_running_loop()

    # --- nashr -------------------------------------------------------
    def publish(self, type_: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        event = {"type": type_, "ts": time.time(), "data": data or {}}
        if type_ == "STATE_CHANGE":
            self.state = event["data"].get("state", self.state)
        if type_ in ("TRANSCRIPT", "TOOL_CALLED", "LOG"):
            self._history.append(event)
        if type_ in ("METRICS", "SETTINGS", "DEVICES", "CONNECTION"):
            self.snapshot.setdefault(type_, {}).update(event["data"])

        loop = self._loop
        if loop is None or loop.is_closed():
            return event
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            self._fanout(event)
        else:
            loop.call_soon_threadsafe(self._fanout, event)
        return event

    def set_state(self, state: str) -> None:
        if state not in STATES:
            raise ValueError(f"Noma'lum holat: {state}")
        if state != self.state:
            self.publish("STATE_CHANGE", {"state": state})

    def _fanout(self, event: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Sekin iste'molchi: eng eski hodisani tashlab yuboramiz
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    log.debug("Obunachi navbati to'lgan, hodisa tashlab yuborildi: %s", event["type"])

    # --- obuna -------------------------------------------------------
    def subscribe(self, maxsize: int = 500) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)

    # --- buyruqlar ---------------------------------------------------
    def register_command(self, cmd: str, handler: CommandHandler) -> None:
        self._handlers[cmd] = handler

    async def dispatch_command(self, msg: dict[str, Any]) -> dict[str, Any]:
        cmd = msg.get("cmd")
        handler = self._handlers.get(cmd)
        if handler is None:
            return {"ok": False, "error": f"Noma'lum buyruq: {cmd}"}
        try:
            result = await handler(msg)
            return {"ok": True, "cmd": cmd, **(result or {})}
        except Exception as e:
            log.exception("Buyruq bajarilmadi: %s", cmd)
            return {"ok": False, "cmd": cmd, "error": str(e)}


bus = EventBus()
