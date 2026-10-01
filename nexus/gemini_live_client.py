"""Gemini Multimodal Live API (WebSocket) sessiyasi.

Ikki parallel task:
    _send_audio()  — AudioStreamer.frames() → session.send_realtime_input(audio=Blob)
                     (PTT rejimida VAD o'chiq: `activity_start`/`activity_end` markerlari ham shu navbatdan)
    _receive()     — session.receive() → audio ijrosi, transkript, tool chaqiruvlari

`session.receive()` HAR model navbati tugaganda (`turn_complete`) iteratsiyani
tugatadi — bu uzilish EMAS. Shuning uchun `_receive` uni sikl ichida qayta
chaqiradi; birorta xabar kelmagan (bo'sh) iteratsiya — haqiqiy uzilish.
Tool bilan tugagan navbatdan keyin modelning reaksiyasi keyingi iteratsiyada keladi.

Tool chaqiruvlari `_receive` ni bloklamaydi — har biri alohida task'da bajariladi
(`_handle_tool_call`). Uzilishda eksponensial backoff bilan, sessiya resume
handle'i bilan qayta ulanadi (`session_resumption`); `go_away` → yumshoq qayta
ulanish; 5 s dan kam yashagan sessiyaning handle'i tashlanadi.

Wake (ism): `WakeState.should_act(user_text)` False bo'lsa — audio allaqachon
modelga ketgan, lekin javob audiosi ijro etilmaydi va tool chaqiruvlari
`{"ok": false, "output": "not addressed"}` bilan qaytariladi (`_addressed`).

Diktovka: faol bo'lganda model audiosi ijro etilmaydi; foydalanuvchi
transkriptining har final bo'lagi darhol `type_text` tool orqali teriladi;
to'xtash iborasi rejimni tugatadi.

Ishlatilgan SDK (google-genai 2.24) nomlari (introspeksiya bilan tekshirilgan):
`client.aio.live.connect`, `session.send_realtime_input(audio=|activity_start=|activity_end=)`,
`session.send_client_content`, `session.send_tool_response`, `session.receive`;
`types.LiveConnectConfig(session_resumption, context_window_compression,
realtime_input_config, media_resolution, input_audio_transcription, ...)`,
`types.SessionResumptionConfig(handle)`, `types.ContextWindowCompressionConfig(sliding_window)`,
`types.SlidingWindow()`, `types.RealtimeInputConfig(automatic_activity_detection)`,
`types.AutomaticActivityDetection(disabled, start_of_speech_sensitivity,
end_of_speech_sensitivity, prefix_padding_ms, silence_duration_ms)`,
`types.StartSensitivity.START_SENSITIVITY_LOW`, `types.EndSensitivity.END_SENSITIVITY_HIGH`,
`types.MediaResolution.MEDIA_RESOLUTION_HIGH`, `types.AudioTranscriptionConfig(language_codes)`,
`types.ActivityStart/ActivityEnd`; xabar maydonlari: `server_content`
(`interrupted`, `input_transcription{.text,.finished}`, `output_transcription`,
`model_turn`, `generation_complete`, `turn_complete`), `tool_call`,
`tool_call_cancellation`, `go_away{.time_left}`,
`session_resumption_update{.resumable,.new_handle}`.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from nexus.dictation import DictationState
from nexus.events import EventBus
from nexus.wake import MODES, WakeState, ends_conversation, wants_conversation

log = logging.getLogger("nexus.gemini")

STABLE_CONNECTION_S = 30.0  # shuncha vaqt ulanib tursa — backoff hisoblagichi nolga
SHORT_SESSION_S = 5.0  # bundan kam yashagan sessiya — resume handle yaroqsiz deb tashlanadi
SOFT_RECONNECT_DELAY_S = 0.2  # go_away / so'ralgan qayta ulanishda kutish
STUCK_STATE_S = 20.0  # band holat (tool'siz) shuncha vaqt serverdan hech narsa kelmasa — idle ga qaytariladi
DICTATION_PASSTHROUGH_TOOLS = frozenset({"stop_dictation", "start_dictation"})
# Modelga bog'liq konfiguratsiya maydonlari — server rad etsa (1007) shu tartibda olib tashlanadi
CONFIG_FALLBACK_ORDER = ("google_search", "thinking_config", "language_codes", "media_resolution", "activity_handling")
NO_KEY_DETAIL = "API kaliti yo'q — Sozlamalar → Gemini API kaliti"


# ---------------------------------------------------------------------------
# Toza funksiyalar
# ---------------------------------------------------------------------------
def compute_backoff(attempt: int, base: float, max_delay: float, jitter: float | None = None) -> float:
    """base * 2**attempt + jitter, max_delay bilan cheklangan.

    `jitter` None bo'lsa [0, base) oralig'ida tasodifiy qo'shiladi (testlarda 0 beriladi)."""
    attempt = max(0, int(attempt))
    try:
        delay = float(base) * (2.0 ** attempt)
    except OverflowError:
        delay = float(max_delay)
    delay = min(delay, float(max_delay))
    j = random.uniform(0.0, float(base)) if jitter is None else float(jitter)
    return max(0.0, min(delay + j, float(max_delay)))


def should_drop_resume_handle(lived_s: float | None, handle: str | None, short_s: float = SHORT_SESSION_S) -> bool:
    """Sessiya juda qisqa yashagan bo'lsa (masalan, eskirgan handle) — handle tashlanadi."""
    return handle is not None and lived_s is not None and lived_s < short_s


def is_config_rejection(exc: BaseException) -> bool:
    """Server konfiguratsiyani rad etdimi (WebSocket 1007 / invalid argument), kalit xatosi emas?"""
    msg = str(exc)
    low = msg.lower()
    if "api key" in low or "api_key" in low:
        return False
    code = getattr(exc, "code", None)
    if "exceeded your current quota" in low or "resource_exhausted" in low:
        # Google Search grounding kabi qo'shimcha imkoniyatlar bu kalitda kvotasiz bo'lishi mumkin —
        # ularni olib tashlab qayta urinamiz (kvota xatosi ham konfiguratsiyaga bog'liq bo'ladi)
        return True
    return code == 1007 or "1007" in msg or "invalid argument" in low or "invalid_argument" in low


def is_api_key_error(exc: BaseException) -> bool:
    """Server kalitni rad etdimi (noto'g'ri / bekor qilingan API kalit)?"""
    low = str(exc).lower()
    return "api key" in low or "api_key" in low


def thinking_level_for(model: str, level: str | None) -> str | None:
    """`extended-thinking` modelida daraja majburiy (bo'sh bo'lsa "high"); boshqa modelda faqat berilsa."""
    lvl = (level or "").strip().lower()
    if "extended-thinking" in (model or "").lower():
        return lvl or "high"
    return lvl or None


def _to_function_declarations(decls: list[dict[str, Any]]) -> list[Any]:
    from google.genai import types

    out = []
    for d in decls:
        try:
            out.append(types.FunctionDeclaration(**d))
        except Exception as e:  # noqa: BLE001
            log.error("Tool deklaratsiyasi noto'g'ri (%s): %s", d.get("name"), e)
    return out


def _grounding_sources(gm: Any) -> list[str]:
    """`grounding_metadata.grounding_chunks[*].web.{uri,title}` → "title — uri" ro'yxati."""
    out: list[str] = []
    for chunk in getattr(gm, "grounding_chunks", None) or []:
        web = getattr(chunk, "web", None)
        uri = getattr(web, "uri", None) if web is not None else None
        if not uri:
            continue
        title = getattr(web, "title", None)
        out.append(f"{title} — {uri}" if title else str(uri))
    return out


class GeminiConfigError(RuntimeError):
    """Konfiguratsiya xatosi (masalan, API kaliti yo'q)."""


# ---------------------------------------------------------------------------
# Mijoz
# ---------------------------------------------------------------------------
class GeminiLiveClient:
    def __init__(
        self,
        bus: EventBus,
        settings: Any,
        registry: Any,
        audio: Any,
        *,
        wait_for_key: bool = False,
        key_saver: Callable[[str], Path | None] | None = None,
    ) -> None:
        self.bus = bus
        self.settings = settings
        self.registry = registry
        self.audio = audio
        # Kalit yo'q bo'lsa xato bilan chiqish o'rniga UI (Sozlamalar) dan kiritilishini kutish
        self.wait_for_key = wait_for_key
        # `set_api_key` kalitni saqlash funksiyasi (masalan `config.save_api_key`); None — faqat joriy sessiya
        self.key_saver = key_saver
        self._key_changed = asyncio.Event()

        self._session: Any = None
        self._stop = asyncio.Event()
        self._tool_tasks: set[asyncio.Task] = set()
        self._dictation_tasks: set[asyncio.Task] = set()
        self._reconnect_requested = False
        self._reconnect_reason = ""
        self.connected: bool = False

        # Sessiya davomiyligi
        self._resume_handle: str | None = None
        self._go_away_pending = False
        self.reconnects: int = 0
        self._vad_disabled = False  # joriy sessiyada server-VAD o'chiqmi (PTT)
        self._config_fallback = 0  # CONFIG_FALLBACK_ORDER dan nechta maydon olib tashlangan
        self._sources: list[str] = []  # joriy javobning grounding manbalari

        # Transkript yig'uvchilar
        self._user_text = ""
        self._assistant_text = ""

        # Latency: foydalanuvchi gapi tugagan payt → birinchi audio chunk
        self._turn_start_ts: float | None = None
        self._first_audio_reported = False
        self.last_latency_ms: int | None = None

        # Wake va diktovka
        self.wake = WakeState(
            name=str(getattr(settings, "wake_name", "Nexus") or ""),
            mode=str(getattr(settings, "wake_mode", "name") or "name"),
            follow_up_s=float(getattr(settings, "wake_follow_up_s", 8.0) or 8.0),
            conversation_idle_s=float(getattr(settings, "conversation_idle_s", 45.0) or 45.0),
        )
        self.dictation = DictationState()
        self._addressed = True  # joriy navbat yordamchiga qaratilganmi
        # Javobni oxirigacha yetkazish: yordamchiga qaratilgan buyruq javobi tugaguncha (turn_complete)
        # fon ovozlarining transkripti `_addressed` ni False ga tushirib, javob audiosini/toollarni kesmaydi.
        self._turn_locked = False
        self._model_turn_active = False  # model hozir javob beryapti (turn_complete hali kelmagan)
        self._queued_addressed: bool | None = None  # javob paytida aytilgan gap — keyingi navbat uchun qaror
        self._drop_turn_audio = False  # "to'xtatish" bosildi — joriy javobning qolgan audiosi ijro etilmaydi
        self._last_activity = time.monotonic()  # oxirgi server xabari / foydalanuvchi navbati (watchdog)

        self.bus.register_command("text", self._cmd_text)
        # `kill_all` buyrug'ini ToolRegistry boshqaradi (tool tasklar + kutilayotgan tasdiq);
        # klient faqat ilgak orqali o'z tasklarini bekor qiladi. Registry yo'q bo'lsa — zaxira handler.
        if registry is not None:
            try:
                registry.on_kill_all = self._on_kill_all
            except AttributeError:  # o'zgarmas soxta registry
                self.bus.register_command("kill_all", self._cmd_kill_all)
        else:
            self.bus.register_command("kill_all", self._cmd_kill_all)
        self.bus.register_command("wake_mode", self._cmd_wake_mode)
        self.bus.register_command("set_name", self._cmd_set_name)
        self.bus.register_command("dictation", self._cmd_dictation)
        self.bus.register_command("conversation", self._cmd_conversation)
        self.bus.register_command("set_api_key", self._cmd_set_api_key)
        self.bus.register_command("interrupt", self._cmd_interrupt)

        self.publish_settings()

        # Audio ilgaklari (PTT)
        if hasattr(self.audio, "on_ptt_mode_change"):
            self.audio.on_ptt_mode_change = self._on_ptt_mode_change
        if hasattr(self.audio, "on_ptt_press"):
            self.audio.on_ptt_press = self._on_ptt_press

    # --- konfiguratsiya ----------------------------------------------
    def _build_config(self) -> Any:
        from google.genai import types

        try:
            from nexus.tools.schemas import SYSTEM_INSTRUCTION
        except Exception:  # noqa: BLE001
            SYSTEM_INSTRUCTION = (
                "Sen Nexus — macOS uchun o'zbek tilida gaplashadigan ovozli yordamchisan. "
                "Qisqa va aniq javob ber."
            )
        decls: list[dict[str, Any]] = []
        if self.registry is not None and hasattr(self.registry, "declarations"):
            try:
                decls = list(self.registry.declarations())
            except Exception as e:  # noqa: BLE001
                log.error("Tool deklaratsiyalari olinmadi: %s", e)
        fds = _to_function_declarations(decls)
        tools: list[Any] = [types.Tool(function_declarations=fds)] if fds else []
        s = self.settings
        dropped = set(CONFIG_FALLBACK_ORDER[: self._config_fallback])
        if getattr(s, "google_search_grounding", False) and "google_search" not in dropped:
            # Live API bir ro'yxatda function_declarations va google_search ni qabul qiladi (alohida Tool obyektlari)
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        langs = list(getattr(s, "transcription_language_list", None) or [])
        if "language_codes" in dropped:
            langs = []
        input_tr = types.AudioTranscriptionConfig(language_codes=langs or None)

        # Server-VAD; PTT rejimida o'chiq — activity_start/end o'zimiz yuboramiz
        self._vad_disabled = bool(getattr(self.audio, "ptt_mode", False))
        if self._vad_disabled:
            aad = types.AutomaticActivityDetection(disabled=True)
        else:
            start_name = f"START_SENSITIVITY_{str(getattr(s, 'vad_start_sensitivity', 'LOW')).upper()}"
            end_name = f"END_SENSITIVITY_{str(getattr(s, 'vad_end_sensitivity', 'HIGH')).upper()}"
            aad = types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=getattr(
                    types.StartSensitivity, start_name, types.StartSensitivity.START_SENSITIVITY_LOW
                ),
                end_of_speech_sensitivity=getattr(
                    types.EndSensitivity, end_name, types.EndSensitivity.END_SENSITIVITY_HIGH
                ),
                prefix_padding_ms=int(getattr(s, "vad_prefix_ms", 150)),
                silence_duration_ms=int(getattr(s, "vad_silence_ms", 500)),
            )

        kwargs: dict[str, Any] = {}
        if getattr(s, "session_resumption", True):
            kwargs["session_resumption"] = types.SessionResumptionConfig(handle=self._resume_handle)
        if getattr(s, "context_compression", True):
            kwargs["context_window_compression"] = types.ContextWindowCompressionConfig(
                sliding_window=types.SlidingWindow()
            )
        level = thinking_level_for(s.gemini_model, getattr(s, "thinking_level", None))
        if level and "thinking_config" not in dropped:
            tl = getattr(types.ThinkingLevel, level.upper(), None) or level  # ThinkingLevel.LOW/MEDIUM/HIGH
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=tl)
        if "media_resolution" not in dropped:
            kwargs["media_resolution"] = types.MediaResolution.MEDIA_RESOLUTION_HIGH
        ric_kwargs: dict[str, Any] = {}
        if not self.allow_interrupt and "activity_handling" not in dropped:
            # Foydalanuvchi (yoki xonadagi boshqa ovoz) gapirsa ham javob uzilmaydi — keyingi gap navbatga
            ric_kwargs["activity_handling"] = types.ActivityHandling.NO_INTERRUPTION

        # DIQQAT: enable_affective_dialog ISHLATILMAYDI (1007 xato), TEXT modality ham (1007).
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=SYSTEM_INSTRUCTION,
            tools=tools,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=s.gemini_voice)
                )
            ),
            input_audio_transcription=input_tr,
            output_audio_transcription=types.AudioTranscriptionConfig(),
            realtime_input_config=types.RealtimeInputConfig(automatic_activity_detection=aad, **ric_kwargs),
            **kwargs,
        )

    def _apply_config_fallback(self, exc: BaseException, lived: float | None) -> bool:
        """Server konfiguratsiyani rad etgan bo'lsa navbatdagi modelga bog'liq maydonni olib tashlaydi."""
        if not is_config_rejection(exc) or (lived is not None and lived >= SHORT_SESSION_S):
            return False
        # Faol bo'lmagan maydonlarni (masalan grounding o'chiq bo'lsa google_search) o'tkazib yuboramiz
        while self._config_fallback < len(CONFIG_FALLBACK_ORDER):
            candidate = CONFIG_FALLBACK_ORDER[self._config_fallback]
            if (candidate == "google_search" and not getattr(self.settings, "google_search_grounding", False)) or (
                candidate == "activity_handling" and self.allow_interrupt
            ):
                self._config_fallback += 1
                continue
            break
        if self._config_fallback >= len(CONFIG_FALLBACK_ORDER):
            return False
        field = CONFIG_FALLBACK_ORDER[self._config_fallback]
        self._config_fallback += 1
        msg = f"Server konfiguratsiyani rad etdi — '{field}' siz qayta urinamiz"
        log.warning(msg)
        self.bus.publish("LOG", {"level": "warn", "message": msg})
        return True

    # --- asosiy sikl ----------------------------------------------------
    async def run(self) -> None:
        """Cheksiz ulanish sikli; `stop()` chaqirilguncha qayta ulanaveradi."""
        if not self._api_key():
            if not self.wait_for_key:
                msg = (
                    "GEMINI_API_KEY bo'sh yoki namunaviy (your_api_key_here). `.env` fayliga haqiqiy "
                    "GEMINI_API_KEY=... qo'ying (https://aistudio.google.com/apikey dan oling) va qayta ishga tushiring."
                )
                self.bus.publish("LOG", {"level": "error", "message": msg})
                self.bus.publish("CONNECTION", {"gemini": "disconnected", "attempt": 0, "detail": "API kaliti yo'q"})
                raise GeminiConfigError(msg)
            await self._wait_for_api_key()
            if self._stop.is_set():
                self.bus.publish("CONNECTION", {"gemini": "disconnected", "attempt": 0, "detail": "to'xtatildi"})
                return

        from google import genai

        client: Any = None
        client_key = ""
        self.publish_settings()
        attempt = 0
        ever_connected = False
        while not self._stop.is_set():
            if self._key_changed.is_set():
                self._key_changed.clear()
                attempt = 0  # yangi kalit — backoff boshidan
            key = self._api_key()
            if client is None or key != client_key:
                # Kalit Sozlamalardan almashtirilgan bo'lsa mijoz yangi kalit bilan qayta quriladi
                client = self.settings.make_client() if hasattr(self.settings, "make_client") else genai.Client(api_key=key)
                client_key = key
            self._reconnect_requested = False
            self._go_away_pending = False
            connected_at: float | None = None
            self._audio_call("pause_upstream")  # ulanmaguncha mikrofon navbatga yig'ilmasin
            error: BaseException | None = None
            try:
                if attempt:
                    self.bus.publish("CONNECTION", {"gemini": "reconnecting", "attempt": attempt, "detail": ""})
                config = self._build_config()
                async with client.aio.live.connect(model=self.settings.gemini_model, config=config) as session:
                    connected_at = time.monotonic()
                    self._session = session
                    self.connected = True
                    if ever_connected:
                        self.reconnects += 1
                        self._publish_metrics(reconnects=self.reconnects)
                    ever_connected = True
                    self._audio_call("resume_upstream")  # drain + davom
                    resumed = " (davom ettirildi)" if self._resume_handle else ""
                    self.bus.publish(
                        "CONNECTION",
                        {"gemini": "connected", "attempt": attempt, "detail": self.settings.gemini_model},
                    )
                    self.bus.publish(
                        "LOG", {"level": "info", "message": f"Gemini ulandi: {self.settings.gemini_model}{resumed}"}
                    )
                    self.bus.set_state(self._idle_state())
                    await self._session_loop(session)
            except asyncio.CancelledError:
                raise
            except GeminiConfigError:
                raise
            except Exception as e:  # noqa: BLE001
                error = e
                detail = f"{type(e).__name__}: {e}"
                log.warning("Gemini sessiyasi uzildi: %s", detail)
                if is_api_key_error(e):
                    self.bus.publish(
                        "LOG",
                        {"level": "error", "message": "API kalit rad etildi — Sozlamalar → Gemini API kalitini yangilang"},
                    )
                else:
                    self.bus.publish("LOG", {"level": "warn", "message": f"Gemini uzildi: {detail}"})
            finally:
                self._session = None
                self.connected = False
                self._reset_turn_tracking()
                self._audio_call("pause_upstream")
                self.audio.player.clear()
                await self._cancel_tool_tasks()

            if self._stop.is_set():
                break
            lived = None if connected_at is None else time.monotonic() - connected_at
            if error is not None and self._apply_config_fallback(error, lived):
                self.request_reconnect("config_fallback")
            if should_drop_resume_handle(lived, self._resume_handle, SHORT_SESSION_S):
                log.info("Sessiya %.1fs yashadi — resume handle tashlandi", lived or 0.0)
                self._resume_handle = None
            if lived is not None and lived >= STABLE_CONNECTION_S:
                attempt = 0
            if self._reconnect_requested:
                delay = SOFT_RECONNECT_DELAY_S
                attempt = max(attempt, 0)  # yumshoq qayta ulanish backoff'ni oshirmaydi
                self.bus.publish(
                    "CONNECTION",
                    {"gemini": "reconnecting", "attempt": attempt, "detail": self._reconnect_reason or "qayta"},
                )
            else:
                delay = compute_backoff(
                    attempt, self.settings.reconnect_base_delay, self.settings.reconnect_max_delay
                )
                attempt += 1
                self.bus.publish(
                    "CONNECTION",
                    {"gemini": "reconnecting", "attempt": attempt, "detail": f"{delay:.1f}s dan so'ng"},
                )
            if getattr(self.bus, "state", None) != "awaiting_confirmation":  # UI dan boshlangan tasdiq kartasini buzmaymiz
                self.bus.set_state(self._idle_state())
            await self._sleep_unless_woken(delay)

        self.bus.publish("CONNECTION", {"gemini": "disconnected", "attempt": 0, "detail": "to'xtatildi"})

    def _api_key(self) -> str:
        return (getattr(self.settings, "gemini_api_key", "") or "").strip()

    async def _wait_for_api_key(self) -> None:
        """Kalit Sozlamalardan (`set_api_key`) kiritilguncha yoki `stop()` gacha kutadi."""
        msg = "Gemini API kaliti kiritilmagan — Sozlamalar (⚙) → Gemini API kaliti (https://aistudio.google.com/apikey)"
        log.warning(msg)
        self.bus.publish("LOG", {"level": "warn", "message": msg})
        self.bus.publish("CONNECTION", {"gemini": "disconnected", "attempt": 0, "detail": NO_KEY_DETAIL})
        self.publish_settings()
        while not self._api_key() and not self._stop.is_set():
            self._key_changed.clear()
            await self._sleep_unless_woken(None)

    async def _sleep_unless_woken(self, timeout: float | None) -> None:
        """`timeout` sekund (None — cheksiz) kutadi; `stop()` yoki yangi API kalit uyg'otadi."""
        waiters = [
            asyncio.create_task(self._stop.wait(), name="gemini-stop-wait"),
            asyncio.create_task(self._key_changed.wait(), name="gemini-key-wait"),
        ]
        try:
            await asyncio.wait(waiters, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for w in waiters:
                w.cancel()
            await asyncio.gather(*waiters, return_exceptions=True)

    async def _session_loop(self, session: Any) -> None:
        send_task = asyncio.create_task(self._send_audio(session), name="gemini-send")
        recv_task = asyncio.create_task(self._receive(session), name="gemini-recv")
        stop_task = asyncio.create_task(self._stop.wait(), name="gemini-stop")
        try:
            done, _ = await asyncio.wait(
                {send_task, recv_task, stop_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for t in done:
                if t is not stop_task and t.exception() is not None:
                    raise t.exception()  # type: ignore[misc]
        finally:
            for t in (send_task, recv_task, stop_task):
                if not t.done():
                    t.cancel()
            await asyncio.gather(send_task, recv_task, stop_task, return_exceptions=True)

    async def stop(self) -> None:
        self._stop.set()
        await self._cancel_tool_tasks()
        s = self._session
        if s is not None:
            try:
                await s.close()
            except Exception as e:  # noqa: BLE001
                log.debug("Sessiyani yopishda xato: %s", e)

    def request_reconnect(self, reason: str = "") -> None:
        self._reconnect_requested = True
        self._reconnect_reason = reason
        log.info("Qayta ulanish so'raldi: %s", reason)

    def _audio_call(self, name: str, *args: Any) -> Any:
        fn = getattr(self.audio, name, None)
        if fn is None:
            return None
        try:
            return fn(*args)
        except Exception as e:  # noqa: BLE001
            log.debug("audio.%s xatosi: %s", name, e)
            return None

    def _idle_state(self) -> str:
        return "dictating" if self.dictation.active else "idle"

    # --- yuborish -------------------------------------------------------
    async def _send_audio(self, session: Any) -> None:
        from google.genai import types

        mime = f"audio/pcm;rate={self.settings.input_sample_rate}"
        sent = 0
        async for item in self.audio.frames():
            if self._stop.is_set():
                break
            try:
                if isinstance(item, (bytes, bytearray, memoryview)):
                    await session.send_realtime_input(audio=types.Blob(data=bytes(item), mime_type=mime))
                    sent += 1
                    if sent % 250 == 0:  # ~5 s
                        player = getattr(self.audio, "player", None)
                        self._publish_metrics(
                            audio_dropped=int(getattr(self.audio, "dropped", 0) or 0),
                            playback_underruns=int(getattr(player, "underruns", 0) or 0),
                            playback_xruns=int(getattr(player, "xruns", 0) or 0),
                        )
                elif item == "activity_start":
                    if self._vad_disabled:
                        await session.send_realtime_input(activity_start=types.ActivityStart())
                elif item == "activity_end":
                    if self._vad_disabled:
                        await session.send_realtime_input(activity_end=types.ActivityEnd())
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.warning("Audio yuborilmadi (%s): %s", type(e).__name__, e)
                self.bus.publish("LOG", {"level": "warn", "message": f"Audio yuborilmadi: {e}"})
                raise  # soket o'lgan — sessiya sikli qayta ulaydi

    async def send_text(self, text: str) -> bool:
        """UI dan matn buyrug'i. Sessiya yo'q bo'lsa False."""
        text = (text or "").strip()
        if not text:
            return False
        session = self._session
        if session is None:
            self.bus.publish("LOG", {"level": "warn", "message": "Gemini ulanmagan — matn yuborilmadi"})
            return False
        from google.genai import types

        self.bus.publish("TRANSCRIPT", {"role": "user", "text": text, "final": True})
        self._note_user_turn(text)
        self._addressed = True  # UI dan yozilgan matn — aniq bizga
        self._turn_locked = True
        self.wake.touch()
        self._turn_start_ts = time.monotonic()
        self._first_audio_reported = False
        self.bus.set_state("processing")
        await session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text=text)]), turn_complete=True
        )
        return True

    # --- qabul qilish ---------------------------------------------------
    async def _receive(self, session: Any) -> None:
        """`receive()` har navbatda tugaydi — qayta chaqiramiz; bo'sh iteratsiya = uzilish."""
        while not self._stop.is_set():
            received = False
            async for msg in session.receive():
                received = True
                if self._stop.is_set():
                    return
                await self._handle_message(session, msg)
                if self._go_away_pending:
                    return  # yumshoq qayta ulanish: sessiya konteksti yopiladi, run() qayta uladi
            if not received:
                log.warning("Server oqimni yopdi (bo'sh receive iteratsiyasi)")
                self.bus.publish("LOG", {"level": "warn", "message": "Gemini oqimni yopdi"})
                return

    async def _handle_message(self, session: Any, msg: Any) -> None:
        self._last_activity = time.monotonic()
        sru = getattr(msg, "session_resumption_update", None)
        if sru is not None:
            new_handle = getattr(sru, "new_handle", None)
            if getattr(sru, "resumable", False) and new_handle:
                if new_handle != self._resume_handle:
                    log.debug("Resume handle yangilandi")
                self._resume_handle = new_handle

        sc = getattr(msg, "server_content", None)
        if sc is not None:
            self._handle_server_content(sc)

        tc = getattr(msg, "tool_call", None)
        if tc is not None and getattr(tc, "function_calls", None):
            self._model_turn_active = True
            if self._addressed and not self.dictation.active:
                self._turn_locked = True
                self.bus.set_state("tool_executing")
            task = asyncio.create_task(self._handle_tool_call(session, tc), name="gemini-tool")
            self._tool_tasks.add(task)
            task.add_done_callback(self._tool_tasks.discard)

        tcc = getattr(msg, "tool_call_cancellation", None)
        if tcc is not None:
            ids = list(getattr(tcc, "ids", None) or [])
            log.info("Tool chaqiruvlari bekor qilindi: %s", ids)
            self._registry_cancel_all()

        ga = getattr(msg, "go_away", None)
        if ga is not None:
            time_left = getattr(ga, "time_left", "")
            self.bus.publish("LOG", {"level": "warn", "message": f"Gemini GoAway: {time_left}"})
            self.request_reconnect("go_away")
            self._go_away_pending = True

    def _stop_session_soft(self) -> None:
        # Sessiya siklini tugatish uchun soketni yopamiz — run() qayta uladi (resume handle bilan).
        s = self._session
        if s is not None:
            asyncio.create_task(self._safe_close(s))

    @staticmethod
    async def _safe_close(session: Any) -> None:
        try:
            await session.close()
        except Exception as e:  # noqa: BLE001
            log.debug("Sessiyani yopishda xato: %s", e)

    def _confirmation_pending(self) -> bool:
        """Registry gate'ida (ConfirmationGate) hal qilinmagan tasdiq so'rovi bormi?"""
        gate = getattr(self.registry, "gate", None)
        if gate is None:
            return False
        try:
            return getattr(gate, "pending", None) is not None
        except Exception as e:  # noqa: BLE001
            log.debug("gate.pending xatosi: %s", e)
            return False

    def _note_user_turn(self, text: str, *, utterance: bool = True) -> None:
        """Registry'ga foydalanuvchi navbatini bildiradi: og'zaki tasdiq (note_utterance) va loop guard/taint (new_turn)."""
        reg = self.registry
        if reg is None:
            return
        if utterance and text and hasattr(reg, "note_utterance"):
            try:
                reg.note_utterance(text, time.time())
            except Exception as e:  # noqa: BLE001
                log.warning("note_utterance xatosi: %s", e)
        if hasattr(reg, "new_turn"):
            try:
                reg.new_turn()
            except Exception as e:  # noqa: BLE001
                log.warning("new_turn xatosi: %s", e)

    def _registry_cancel_all(self) -> int:
        try:
            return int(self.registry.cancel_all() or 0)
        except Exception as e:  # noqa: BLE001
            log.warning("cancel_all xatosi: %s", e)
            return 0

    def _handle_server_content(self, sc: Any) -> None:
        dictating = self.dictation.active

        # 1) Uzilish — foydalanuvchi gapirdi: ijro navbatini tozalaymiz, uzoq toollarni bekor qilamiz.
        # "Javobni oxirigacha" rejimida (standart) server odatda uzmaydi (NO_INTERRUPTION); baribir uzsa
        # (masalan konfiguratsiya zaxirasida) — yig'ilgan audio oxirigacha ijro etiladi, toollar to'xtatilmaydi.
        if getattr(sc, "interrupted", None) and not self.allow_interrupt:
            log.info("Interrupted (javobni oxirigacha rejimi) — ijro va toollar davom etadi")
            self._player_call("play_out")
        elif getattr(sc, "interrupted", None):
            self._turn_locked = False
            self._model_turn_active = False
            dropped = self.audio.player.clear()
            awaiting = self.bus.state == "awaiting_confirmation" or self._confirmation_pending()
            # Tasdiq kutilayotganda "ha" deyish ham barge-in — toolni o'ldirmaymiz, holatni yashirmaymiz
            n = 0 if awaiting else self._registry_cancel_all()
            log.debug("Interrupted — %d chunk tashlandi, %d tool bekor", dropped, n)
            if self._assistant_text:
                if self._addressed and not dictating:
                    self.bus.publish("TRANSCRIPT", {"role": "assistant", "text": self._assistant_text, "final": True})
                self._assistant_text = ""
            if self.bus.state != "awaiting_confirmation":
                self.bus.set_state("dictating" if dictating else "listening")

        # 2) Kiruvchi transkript (foydalanuvchi)
        it = getattr(sc, "input_transcription", None)
        if it is not None and getattr(it, "text", None):
            self._user_text += it.text
            self.bus.publish("TRANSCRIPT", {"role": "user", "text": self._user_text, "final": False})
            if not dictating:
                self._evaluate_addressed(self._user_text)
                if self.bus.state in ("idle", "listening"):
                    self.bus.set_state("listening")
            if getattr(it, "finished", False):
                self._finalize_user_turn()

        # 3) Chiquvchi transkript (yordamchi)
        ot = getattr(sc, "output_transcription", None)
        if ot is not None and getattr(ot, "text", None):
            self._model_turn_active = True
            self._assistant_text += ot.text
            if self._addressed and not dictating:
                self.bus.publish("TRANSCRIPT", {"role": "assistant", "text": self._assistant_text, "final": False})

        # 4) Audio
        mt = getattr(sc, "model_turn", None)
        if mt is not None:
            for part in getattr(mt, "parts", None) or []:
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None) if inline is not None else None
                if data:
                    if self._user_text:
                        self._finalize_user_turn()
                    self._model_turn_active = True
                    if self._addressed and not dictating and not self._drop_turn_audio:
                        self._turn_locked = True
                        self._report_first_audio()
                        self.audio.player.enqueue(data)
                        if self.bus.state != "speaking":
                            self.bus.set_state("speaking")
                txt = getattr(part, "text", None)
                if txt:
                    self._assistant_text += txt
                    if self._addressed and not dictating:
                        self.bus.publish(
                            "TRANSCRIPT", {"role": "assistant", "text": self._assistant_text, "final": False}
                        )

        # 4b) Google Search grounding manbalari
        gm = getattr(sc, "grounding_metadata", None)
        if gm is not None:
            sources = _grounding_sources(gm)
            if sources:
                new = [u for u in sources if u not in self._sources]
                self._sources.extend(new)
                if new and self._addressed and not dictating:
                    self.bus.publish(
                        "LOG",
                        {"level": "info", "message": "Manbalar: " + "; ".join(new), "sources": list(new)},
                    )

        # 5) Generatsiya tugadi — prebuffer to'lmagan bo'lsa ham ijro
        if getattr(sc, "generation_complete", None):
            self._player_call("play_out")

        # 6) Navbat tugadi
        if getattr(sc, "turn_complete", None):
            self._player_call("play_out")
            if self._user_text:
                self._finalize_user_turn()
            if self._assistant_text:
                if self._addressed and not dictating:
                    final = {"role": "assistant", "text": self._assistant_text, "final": True}
                    if self._sources:
                        final["sources"] = list(self._sources)
                    self.bus.publish("TRANSCRIPT", final)
                    self.wake.touch()
                    self.wake.expect_answer(_asks_question(self._assistant_text))
                else:
                    log.info("Javob bostirildi (%s): %s", "diktovka" if dictating else "ism aytilmadi",
                             self._assistant_text[:80])
                self._assistant_text = ""
            self._turn_start_ts = None
            self._sources = []
            self._model_turn_active = False
            self._drop_turn_audio = False
            if not self._tool_tasks:
                # Javob to'liq tugadi (tool natijasini kutayotgan navbat emas) — qulf ochiladi.
                # Keyingi navbat uchun qaror: javob paytida aytilgan gap bo'lsa — o'sha paytdagi baho,
                # aks holda follow-up oynasi ochiq bo'lsa — bizga.
                self._turn_locked = False
                queued, self._queued_addressed = self._queued_addressed, None
                self._addressed = queued if queued is not None else self.wake.should_act("")
                self.bus.set_state(self._idle_state())

    def _player_call(self, name: str) -> None:
        fn = getattr(self.audio.player, name, None)
        if fn is not None:
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                log.debug("player.%s xatosi: %s", name, e)

    def _evaluate_addressed(self, text: str, final: bool = False) -> bool:
        """Wake rejimi bo'yicha gap bizga qaratilganmi (qisman transkriptda ham). Baho qaytariladi.

        Qaratilgan javob davom etayotganda (`_turn_locked`) False baho `_addressed` ni o'zgartirmaydi —
        xonadagi boshqa ovoz boshlangan javobni yarim yo'lda o'chirib qo'ymasin.

        Rad javobi ("yo'q, hozircha hech narsa") — javob berilmaydi; `final` bo'lsa follow-up oynasi
        ham yopiladi: yordamchi yana ism bilan chaqirilguncha jim kutadi."""
        self.tick()
        if not self.wake.conversation and wants_conversation(text):
            self.set_conversation(True)  # "kel gaplashamiz" — ismsiz ham suhbat boshlanadi
        # Follow-up oynasi yordamchi ovozi tugagan paytdan hisoblanadi ("Yana nima qilay?" savolidan keyin)
        last_out = self._playback_last_ts()
        if last_out:
            self.wake.extend_to(last_out)
        act = self.wake.should_act(text, at=self._speech_started_at())
        if act and self._dismissal_applies(text):
            act = False
            if final:
                self.wake.release()
                log.info("Rad javobi — ism bilan chaqirilguncha jim kutiladi: %s", text[:80])
                self.bus.publish("LOG", {"level": "info", "message": "Kutyapman — kerak bo'lsa ismimni ayting"})
        if act or not self._turn_locked:
            self._addressed = act
        return act

    def _dismissal_applies(self, text: str) -> bool:
        """"Yo'q / hech narsa kerak emas" rad javobi sifatida qaralsinmi? Suhbat rejimida va tasdiq
        kutilayotganda ("yo'q" — amalni rad etish, ToolRegistry hal qiladi) — yo'q."""
        if self.wake.conversation or self.dictation.active:
            return False
        if self.bus.state == "awaiting_confirmation" or self._confirmation_pending():
            return False
        return self.wake.is_dismissal(text)

    def _speech_started_at(self) -> float | None:
        """Joriy gap boshlangan payt (AudioStreamer RMS gate). Noma'lum yoki eskirgan bo'lsa None."""
        try:
            ts = float(getattr(self.audio, "speech_started_at", 0.0) or 0.0)
        except (TypeError, ValueError):
            return None
        if not ts or time.monotonic() - ts > 60.0:
            return None
        return ts

    def _playback_last_ts(self) -> float:
        try:
            return float(getattr(self.audio.player, "last_output_ts", 0.0) or 0.0)
        except (AttributeError, TypeError, ValueError):
            return 0.0

    def _finalize_user_turn(self) -> None:
        self._last_activity = time.monotonic()
        text = self._user_text
        if text:
            self.bus.publish("TRANSCRIPT", {"role": "user", "text": text, "final": True})
            self._user_text = ""
        # Diktovkada aytilgan "ha" — teriladigan matn, tasdiq emas
        self._note_user_turn(text, utterance=not self.dictation.active)
        if self.dictation.active:
            self._dispatch_dictation(text)
            return
        if text:
            during_reply = self._model_turn_active
            act = self._evaluate_addressed(text, final=True)
            if during_reply:
                # Javob paytida aytilgan gap — hozirgi javob davom etadi, bu gap keyingi navbatda ko'riladi
                self._queued_addressed = act
            if not act:
                log.info("Ism aytilmadi (%s rejimi) — e'tibor berilmaydi: %s", self.wake.mode, text[:80])
            else:
                self._turn_locked = True
                if self.wake.conversation and ends_conversation(text):
                    # Shu gapga (masalan "xayr") hali javob beriladi, keyingisi — yana faqat ism bilan
                    self.set_conversation(False)
        self._turn_start_ts = time.monotonic()
        self._first_audio_reported = False
        if self.bus.state in ("idle", "listening"):
            self.bus.set_state("processing" if self._addressed else "listening")

    def _report_first_audio(self) -> None:
        if self._first_audio_reported or self._turn_start_ts is None:
            return
        self._first_audio_reported = True
        self.last_latency_ms = int((time.monotonic() - self._turn_start_ts) * 1000)
        self._publish_metrics(latency_ms=self.last_latency_ms)

    def _publish_metrics(self, **kv: Any) -> None:
        prev = dict(self.bus.snapshot.get("METRICS") or {})
        prev.update(kv)
        self.bus.publish("METRICS", prev)

    # --- diktovka -------------------------------------------------------
    def _dispatch_dictation(self, text: str) -> None:
        """Final transkript bo'lagini darhol teradi; to'xtash iborasi rejimni tugatadi."""
        text = (text or "").strip()
        if not text:
            return
        to_type, stopped = self.dictation.split_stop(text)
        if to_type:
            task = asyncio.create_task(self._type_out(to_type), name="dictation-type")
            self._dictation_tasks.add(task)
            task.add_done_callback(self._dictation_tasks.discard)
        if stopped:
            self.set_dictation(False)

    async def _type_out(self, text: str) -> None:
        if self.registry is None:
            return
        try:
            result = await self.registry.execute("type_text", {"text": text + " "})
            if isinstance(result, dict) and result.get("ok", False):
                self.dictation.note_typed(text)
            else:
                log.warning("Diktovka terilmadi: %s", (result or {}).get("error") if isinstance(result, dict) else result)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            log.warning("Diktovka terish xatosi: %s", e)

    def set_dictation(self, active: bool) -> bool:
        active = bool(active)
        if active == self.dictation.active:
            return active
        if active:
            self.dictation.start()
            self.audio.player.clear()
            self.bus.publish("LOG", {"level": "info", "message": "Diktovka boshlandi — to'xtatish: \"to'xta\""})
            self.bus.set_state("dictating")
        else:
            self.dictation.stop()
            self.bus.publish(
                "LOG",
                {"level": "info", "message": f"Diktovka tugadi ({self.dictation.typed_chars} belgi terildi)"},
            )
            if self.bus.state == "dictating":
                self.bus.set_state("listening" if self.connected else "idle")
        self.publish_settings()
        return active

    # --- suhbat rejimi ---------------------------------------------------
    def set_conversation(self, active: bool, reason: str = "", follow_up: bool = True) -> bool:
        """Suhbat rejimi: ismsiz erkin suhbat; jimlikdan keyin o'zi tugaydi (`tick`)."""
        active = bool(active)
        if active == self.wake.conversation:
            if active:
                self.wake.start_conversation()  # oynani yangilash
            return active
        if active:
            self.wake.start_conversation()
            self._addressed = True
            msg = "Suhbat rejimi yoqildi — ismsiz gapirish mumkin (tugatish: \"bo'ldi, rahmat\")"
        else:
            # Aniq tugatilganda xayrlashuv javobi uchun qisqa oyna qoladi (jimlikda — yo'q)
            self.wake.stop_conversation(follow_up=follow_up)
            msg = "Suhbat rejimi tugadi" + (f" ({reason})" if reason else "") + " — endi faqat ism bilan"
        log.info(msg)
        self.bus.publish("LOG", {"level": "info", "message": msg})
        self.publish_settings()
        return active

    def tick(self) -> None:
        """Davriy tekshiruv (MetricsTicker): jimlik tufayli suhbat rejimini tugatish; osilib qolgan holat."""
        self._watchdog()
        playing = bool(getattr(getattr(self.audio, "player", None), "is_playing", False))
        if self.wake.conversation and playing:
            self.wake.touch()  # yordamchi gapiryapti — jimlik hisoblanmaydi
        elif self.wake.conversation_expired:
            self.set_conversation(False, reason=f"{int(self.wake.conversation_idle_s)} s jimlik", follow_up=False)

    def _watchdog(self) -> None:
        """Band holat (processing / tool_executing / speaking) tool ham, ijro ham, server xabari ham
        bo'lmasa `STUCK_STATE_S` dan keyin idle ga qaytariladi: bu holatda mikrofon bostiriladi —
        yordamchi "ishlamay qolgandek" ko'rinmasin."""
        if self.bus.state not in ("processing", "tool_executing", "speaking") or self._tool_tasks:
            return
        if bool(getattr(getattr(self.audio, "player", None), "is_playing", False)):
            return
        idle_for = time.monotonic() - self._last_activity
        if idle_for < STUCK_STATE_S:
            return
        log.warning("Holat %r %.0f s o'zgarmadi (javob kelmadi) — idle ga qaytarildi", self.bus.state, idle_for)
        self.bus.publish("LOG", {"level": "warn", "message": "Javob kelmadi — qayta tinglayapman"})
        self._reset_turn_tracking()
        self._last_activity = time.monotonic()
        self.bus.set_state(self._idle_state())

    async def _cmd_conversation(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"conversation": self.set_conversation(bool(msg.get("value", True)), reason="qo'lda")}

    # --- wake -----------------------------------------------------------
    def publish_settings(self) -> dict[str, Any]:
        data = dict(self.bus.snapshot.get("SETTINGS") or {})
        key = self._api_key()
        data.update({
            "wake_mode": self.wake.mode, "name": self.wake.name, "dictating": self.dictation.active,
            "conversation": self.wake.conversation, "allow_interrupt": self.allow_interrupt,
            "api_key_set": bool(key), "api_key_hint": _key_hint(key),
        })
        self.bus.publish("SETTINGS", data)
        return data

    # --- PTT ilgaklari ----------------------------------------------------
    def _on_ptt_mode_change(self, enabled: bool) -> None:
        # VAD konfiguratsiyasi ulanish paytida beriladi — o'zgarganda qayta ulanamiz (resume handle bilan)
        if self._session is not None and bool(enabled) != self._vad_disabled:
            self.request_reconnect("ptt")
            self._stop_session_soft()

    def _on_ptt_press(self, pressed: bool) -> None:
        if not self._vad_disabled:
            return
        push = getattr(self.audio, "push_marker", None)
        if push is not None:
            push("activity_start" if pressed else "activity_end")

    # --- tool chaqiruvlari ----------------------------------------------
    async def _handle_tool_call(self, session: Any, tool_call: Any) -> list[dict[str, Any]]:
        """Har bir function_call ni registry orqali bajaradi va javobni sessiyaga yuboradi.

        Qaytarilgan ro'yxat — yuborilgan javoblarning dict ko'rinishi (test uchun)."""
        from google.genai import types

        calls = list(getattr(tool_call, "function_calls", None) or [])
        if not calls:
            return []
        addressed = self._addressed
        dictating = self.dictation.active
        if addressed and not dictating:
            self.bus.set_state("tool_executing")

        async def _one(fc: Any) -> dict[str, Any]:
            name = getattr(fc, "name", "") or ""
            args = dict(getattr(fc, "args", None) or {})
            if not addressed and name not in DICTATION_PASSTHROUGH_TOOLS:
                log.info("Tool rad etildi (ism aytilmadi): %s", name)
                return {"id": getattr(fc, "id", None), "name": name, "response": {"ok": False, "output": "not addressed"}}
            if dictating and name not in DICTATION_PASSTHROUGH_TOOLS:
                log.info("Tool rad etildi (diktovka): %s", name)
                return {
                    "id": getattr(fc, "id", None), "name": name,
                    "response": {"ok": False, "output": "dictation mode — ignored"},
                }
            try:
                result = await self.registry.execute(name, args)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.exception("Tool bajarilmadi: %s", name)
                result = {"ok": False, "output": "", "error": str(e), "duration_ms": 0}
            response = {
                "ok": bool(result.get("ok", False)),
                "output": str(result.get("output", "") or ""),
            }
            if result.get("error"):
                response["error"] = str(result["error"])
            for extra in ("note", "next_step"):
                if result.get(extra):
                    response[extra] = str(result[extra])
            if response["ok"]:
                self.wake.touch()
            return {"id": getattr(fc, "id", None), "name": name, "response": response}

        results = await asyncio.gather(*(_one(fc) for fc in calls))
        responses = [
            types.FunctionResponse(id=r["id"], name=r["name"], response=r["response"]) for r in results
        ]
        try:
            await session.send_tool_response(function_responses=responses)
        except Exception as e:  # noqa: BLE001
            log.warning("Tool javobi yuborilmadi: %s", e)
        if self.bus.state == "tool_executing":
            self.bus.set_state("processing")
        return results

    async def _cancel_tool_tasks(self) -> None:
        tasks = list(self._tool_tasks) + list(self._dictation_tasks)
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tool_tasks.clear()
        self._dictation_tasks.clear()

    # --- bus buyruqlari -------------------------------------------------
    async def _cmd_text(self, msg: dict[str, Any]) -> dict[str, Any]:
        ok = await self.send_text(str(msg.get("value", "")))
        return {"sent": ok}

    async def _on_kill_all(self) -> None:
        """ToolRegistry.kill_all() ilgagi: klient tool tasklari bekor, ijro navbati tozalanadi."""
        await self._cancel_tool_tasks()
        self._player_call("clear")
        if self._model_turn_active:
            self._drop_turn_audio = True  # javob hali oqib kelyapti — qolgani ijro etilmasin
        self._turn_locked = False
        self._queued_addressed = None
        # gate.cancel_pending() holatni "processing" ga o'tkazadi; Gemini'ga javob yuborilmaydi —
        # spinner osilib qolmasin.
        if self.bus.state in ("tool_executing", "processing", "awaiting_confirmation"):
            self.bus.set_state(self._idle_state())

    async def _cmd_kill_all(self, _msg: dict[str, Any]) -> dict[str, Any]:
        """Zaxira: registry bo'lmaganda (toolsiz rejim) `kill_all` buyrug'i."""
        n = self._registry_cancel_all() if self.registry is not None else 0
        await self._on_kill_all()
        return {"cancelled": n}

    async def _cmd_wake_mode(self, msg: dict[str, Any]) -> dict[str, Any]:
        mode = str(msg.get("value", "") or "").strip().lower()
        if mode not in MODES:
            raise ValueError(f"Noma'lum wake rejimi: {mode!r} (always|name|smart)")
        self.wake.set_mode(mode)
        if mode == "always":
            self._addressed = True
        self.publish_settings()
        return {"wake_mode": self.wake.mode}

    async def _cmd_set_name(self, msg: dict[str, Any]) -> dict[str, Any]:
        name = str(msg.get("value", "") or "").strip()
        if not name:
            raise ValueError("Ism bo'sh bo'lishi mumkin emas")
        self.wake.set_name(name)
        self.publish_settings()
        return {"name": self.wake.name}

    async def _cmd_dictation(self, msg: dict[str, Any]) -> dict[str, Any]:
        active = self.set_dictation(bool(msg.get("value", True)))
        return {"dictating": active}

    # --- API kalit va "javobni oxirigacha" rejimi -------------------------
    @property
    def allow_interrupt(self) -> bool:
        return bool(getattr(self.settings, "allow_interrupt", False))

    def _reset_turn_tracking(self) -> None:
        self._turn_locked = False
        self._model_turn_active = False
        self._queued_addressed = None
        self._drop_turn_audio = False

    async def _cmd_set_api_key(self, msg: dict[str, Any]) -> dict[str, Any]:
        """UI (Sozlamalar) dan API kalit: tekshiradi, saqlaydi va sessiyani yangi kalit bilan qayta ulaydi."""
        from nexus.config import validate_api_key

        key = validate_api_key(str(msg.get("value", "") or ""))
        path: Path | None = None
        persisted = self.key_saver is not None
        if persisted:
            path = await asyncio.to_thread(self.key_saver, key)
        self.settings.gemini_api_key = key
        os.environ["GEMINI_API_KEY"] = key
        self._resume_handle = None  # eski kalit sessiyasining handle'i yangi kalitga yaramaydi
        self._key_changed.set()
        if self._session is not None:
            self.request_reconnect("api_key")
            self._stop_session_soft()
        log.info("API kalit yangilandi (%s)%s", _key_hint(key), f" → {path}" if path else "")
        self.bus.publish("LOG", {"level": "info", "message": "API kalit saqlandi — Gemini'ga ulanmoqda"})
        self.publish_settings()
        return {"api_key_hint": _key_hint(key), "persisted": persisted}

    def set_allow_interrupt(self, value: bool) -> bool:
        value = bool(value)
        if value == self.allow_interrupt:
            return value
        self.settings.allow_interrupt = value
        if hasattr(self.audio, "barge_in"):
            self.audio.barge_in = value
        # activity_handling ulanish konfiguratsiyasida — o'zgarganda qayta ulanamiz (resume handle bilan)
        if self._session is not None:
            self.request_reconnect("interrupt")
            self._stop_session_soft()
        msg = (
            "Gapni bo'lish yoqildi — javob paytida gapirsangiz yordamchi to'xtaydi"
            if value
            else "Javobni oxirigacha rejimi — har bir buyruq tugagach keyingisiga o'tiladi"
        )
        self.bus.publish("LOG", {"level": "info", "message": msg})
        self.publish_settings()
        return value

    async def _cmd_interrupt(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"allow_interrupt": self.set_allow_interrupt(bool(msg.get("value", False)))}


def _asks_question(text: str) -> bool:
    """Yordamchi javobi foydalanuvchidan javob kutadimi ("Yana nima qilay?", "Labbay, sizni eshitaman")?"""
    t = (text or "").strip().lower()
    return t.endswith("?") or any(w in t for w in ("eshitaman", "слушаю", "listening"))


def _key_hint(key: str) -> str:
    from nexus.config import api_key_hint

    return api_key_hint(key)
