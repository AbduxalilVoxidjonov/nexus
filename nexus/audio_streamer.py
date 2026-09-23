"""Mikrofon oqimi va ovoz ijrosi (sounddevice / PortAudio).

`AudioStreamer` — mikrofondan 16 kHz int16 mono PCM chunklarni o'qib
`asyncio.Queue` ga qo'yadi (`frames()` async generator orqali Gemini'ga
uzatiladi) va UI uchun `AUDIO_LEVEL` hodisalarini nashr qiladi.

`AudioPlayer` — Gemini'dan kelgan 24 kHz int16 mono PCM'ni ijro etadi;
prebuffer (~220 ms) yig'ilgach ijro boshlanadi (jitter), `play_out()` qolganini
darhol chiqaradi (navbat tugaganda), `clear()` navbatni tozalaydi (barge-in).

Echo guard: yordamchi gapirayotganda (`player.is_playing`) mikrofon chunklari
o'rniga sukunat yuboriladi — server VAD o'z ovozini eshitmasin; lekin RMS
bo'sag'aning `echo_barge_factor` barobaridan baland bo'lsa (foydalanuvchi
gapiryapti) chunk o'tkaziladi (barge-in saqlanadi).

Toza (side-effect'siz) funksiyalar — `compute_rms`, `should_forward`,
`gate_open`, `echo_gate` — testlarda alohida tekshiriladi.
"""
from __future__ import annotations

import asyncio
import logging
import math
import threading
import time
from collections import deque
from collections.abc import AsyncIterator, Callable
from typing import Any, Self

import numpy as np

try:  # CI / audio'siz muhitlarda import xatosi bo'lishi mumkin
    import sounddevice as sd
except Exception as _sd_err:  # noqa: BLE001  # pragma: no cover - muhitga bog'liq
    sd = None  # type: ignore[assignment]
    _SD_IMPORT_ERROR: Exception | None = _sd_err
else:
    _SD_IMPORT_ERROR = None

from nexus.events import EventBus

log = logging.getLogger("nexus.audio")

MIC_PERMISSION_HINT = (
    "Mikrofonga ruxsat berilmagan bo'lishi mumkin: "
    "Tizim sozlamalari → Maxfiylik va xavfsizlik → Mikrofon"
)

MIN_DB = -60.0
LEVEL_PUBLISH_HZ = 20  # AUDIO_LEVEL sekundiga ~20 marta


# ---------------------------------------------------------------------------
# Toza funksiyalar
# ---------------------------------------------------------------------------
def compute_rms(pcm: bytes) -> tuple[float, float]:
    """int16 mono PCM baytlaridan (rms 0..1, db -60..0) qaytaradi."""
    if not pcm or len(pcm) < 2:
        return 0.0, MIN_DB
    samples = np.frombuffer(pcm[: len(pcm) - (len(pcm) % 2)], dtype=np.int16).astype(np.float32)
    if samples.size == 0:
        return 0.0, MIN_DB
    rms = float(np.sqrt(np.mean(samples * samples)) / 32768.0)
    rms = max(0.0, min(1.0, rms))
    if rms <= 0.0:
        return 0.0, MIN_DB
    db = 20.0 * math.log10(rms)
    db = max(MIN_DB, min(0.0, db))
    return rms, db


def should_forward(muted: bool, ptt_mode: bool, ptt_pressed: bool) -> bool:
    """Chunk Gemini'ga yuborilsinmi? (mute yoki PTT bosilmagan bo'lsa — yo'q)."""
    if muted:
        return False
    return not (ptt_mode and not ptt_pressed)


def sensitivity_to_threshold(sensitivity: float, base: float = 0.02) -> float:
    """Sezgirlik (0..1) → RMS bo'sag'asi. 1.0 = juda sezgir (past bo'sag'a)."""
    s = max(0.0, min(1.0, sensitivity))
    # log shkala: 0 → base*5, 0.5 → base, 1 → base/5
    return base * (5.0 ** (1.0 - 2.0 * s))


def gate_open(rms: float, threshold: float) -> bool:
    return rms >= threshold


def echo_gate(rms: float, threshold: float, playing: bool, guard: bool = True, factor: float = 3.0) -> bool:
    """Yordamchi gapirayotganda mikrofon chunk'i o'tkazilsinmi?

    True = o'tkaz. Guard o'chiq yoki ijro yo'q bo'lsa — doim True. Ijro paytida
    faqat RMS >= threshold*factor bo'lsa (foydalanuvchi aniq gapiryapti — barge-in)."""
    if not guard or not playing:
        return True
    return rms >= float(threshold) * float(factor)


# Mikrofon navbatiga qo'yiladigan boshqaruv markerlari (PTT rejimida VAD o'chiq bo'lganda)
MARK_ACTIVITY_START = "activity_start"
MARK_ACTIVITY_END = "activity_end"
PLAYING_TAIL_S = 0.25  # oxirgi real chunk chiqqach shuncha vaqt "ijro" deb hisoblanadi


# ---------------------------------------------------------------------------
# Yordamchi
# ---------------------------------------------------------------------------
def _require_sd() -> Any:
    if sd is None:
        raise RuntimeError(f"sounddevice yuklanmadi: {_SD_IMPORT_ERROR}. PortAudio o'rnatilganmi?")
    return sd


def _default_input_index() -> int | None:
    """sounddevice standart kirish qurilmasi indeksi (`_InputOutputPair` yoki int)."""
    if sd is None:
        return None
    try:
        dev = sd.default.device
        idx = dev[0] if hasattr(dev, "__getitem__") else dev
        return int(idx) if idx is not None and int(idx) >= 0 else None
    except Exception:  # noqa: BLE001
        return None


def list_input_devices() -> list[dict[str, Any]]:
    """[{"index", "name", "default"}] — faqat kirish (mikrofon) qurilmalari."""
    if sd is None:
        return []
    try:
        devices = sd.query_devices()
        default_in = _default_input_index()
    except Exception as e:  # noqa: BLE001
        log.warning("Qurilmalar ro'yxati olinmadi: %s", e)
        return []
    out: list[dict[str, Any]] = []
    for idx, dev in enumerate(devices):
        if int(dev.get("max_input_channels", 0)) <= 0:
            continue
        out.append({"index": idx, "name": str(dev.get("name", f"#{idx}")), "default": idx == default_in})
    return out


def resolve_device(name_or_index: str | int | None) -> int | None:
    """Nom (qism mos kelsa ham) yoki indeks → qurilma indeksi. None = standart."""
    if name_or_index is None or name_or_index == "":
        return None
    if isinstance(name_or_index, int):
        return name_or_index
    s = str(name_or_index).strip()
    if s.isdigit():
        return int(s)
    for d in list_input_devices():
        if s.lower() in d["name"].lower():
            return d["index"]
    log.warning("Qurilma topilmadi: %r — standart qurilma ishlatiladi", s)
    return None


# ---------------------------------------------------------------------------
# Ijro
# ---------------------------------------------------------------------------
class AudioPlayer:
    """24 kHz int16 mono ijro. `enqueue` istalgan thread/task'dan chaqirilishi mumkin.

    `prebuffer_ms` > 0 bo'lsa, birinchi chunklar yig'ilib (armed) keyin ijro
    boshlanadi; `play_out()` bufer to'lmasa ham ijroni boshlaydi."""

    def __init__(
        self,
        sample_rate: int = 24000,
        enabled: bool = True,
        bus: EventBus | None = None,
        prebuffer_ms: int = 0,
    ) -> None:
        self.sample_rate = sample_rate
        self.enabled = enabled
        self._bus = bus
        self._queue: deque[bytes] = deque()
        self._lock = threading.Lock()
        self._leftover = b""
        self._stream: Any = None
        self.prebuffer_ms = max(0, int(prebuffer_ms))
        self._prebuffer_bytes = int(self.sample_rate * self.prebuffer_ms / 1000) * 2
        self._armed = self._prebuffer_bytes == 0
        self._pending = 0  # navbat + leftover baytlar
        self._last_out_ts = 0.0  # oxirgi real (nol bo'lmagan) chunk chiqqan payt
        self.chunks_played = 0

    # --- hayot sikli ---
    def start(self) -> None:
        if not self.enabled or self._stream is not None:
            return
        try:
            s = _require_sd()
            self._stream = s.RawOutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=int(self.sample_rate * 0.02),  # 20 ms
                callback=self._callback,
            )
            self._stream.start()
            log.info("Ovoz chiqish oqimi ochildi (%d Hz)", self.sample_rate)
        except Exception as e:  # noqa: BLE001
            self._stream = None
            self.enabled = False
            log.error("Ovoz chiqish oqimi ochilmadi: %s", e)
            if self._bus:
                self._bus.publish("LOG", {"level": "warn", "message": f"Ovoz ijrosi o'chirildi: {e}"})

    def stop(self) -> None:
        st, self._stream = self._stream, None
        if st is not None:
            try:
                st.stop()
                st.close()
            except Exception as e:  # noqa: BLE001
                log.debug("Oqimni yopishda xato: %s", e)
        self.clear()

    # --- navbat ---
    def enqueue(self, data: bytes) -> None:
        if not data:
            return
        with self._lock:
            self._queue.append(bytes(data))
            self._pending += len(data)
            if not self._armed and self._pending >= self._prebuffer_bytes:
                self._armed = True

    def play_out(self) -> None:
        """Buferdagi qolgan audioni (prebuffer to'lmagan bo'lsa ham) ijroga qo'yib yuboradi."""
        with self._lock:
            if self._pending:
                self._armed = True

    def clear(self) -> int:
        """Navbatni tozalaydi (interruption). Tashlangan chunklar sonini qaytaradi."""
        with self._lock:
            n = len(self._queue)
            self._queue.clear()
            self._leftover = b""
            self._pending = 0
            self._armed = self._prebuffer_bytes == 0
            self._last_out_ts = 0.0
        return n

    def pending_bytes(self) -> int:
        with self._lock:
            return self._pending

    @property
    def armed(self) -> bool:
        return self._armed

    @property
    def is_playing(self) -> bool:
        """Hozir ovoz chiqyaptimi (navbatda audio bor yoki oxirgi chunk yaqinda chiqqan)."""
        with self._lock:
            if self._pending:
                return True
            return bool(self._last_out_ts) and (time.monotonic() - self._last_out_ts) < PLAYING_TAIL_S

    # --- PortAudio callback (alohida thread) ---
    def _callback(self, outdata: Any, frames: int, time_info: Any, status: Any) -> None:
        need = frames * 2  # int16 mono
        buf = bytearray()
        with self._lock:
            if self._armed:
                if self._leftover:
                    buf += self._leftover
                    self._leftover = b""
                while len(buf) < need and self._queue:
                    buf += self._queue.popleft()
                if len(buf) > need:
                    self._leftover = bytes(buf[need:])
                    del buf[need:]
                self._pending = max(0, self._pending - len(buf))
                if buf:
                    self._last_out_ts = time.monotonic()
                    self.chunks_played += 1
                if self._pending == 0 and self._prebuffer_bytes:
                    # Bufer bo'shadi — keyingi javob yana prebuffer bilan boshlansin
                    self._armed = False
            if len(buf) < need:
                # Navbat bo'sh (yoki hali armed emas) — nol (sukunat) bilan to'ldiramiz
                buf += b"\x00" * (need - len(buf))
        outdata[:] = bytes(buf)


# ---------------------------------------------------------------------------
# Mikrofon
# ---------------------------------------------------------------------------
class AudioStreamer:
    """Mikrofon → asyncio.Queue → Gemini. AUDIO_LEVEL va gate holatini nashr qiladi."""

    def __init__(self, bus: EventBus, settings: Any, loop: asyncio.AbstractEventLoop | None = None) -> None:
        self.bus = bus
        self.settings = settings
        self.sample_rate: int = int(settings.input_sample_rate)
        self.chunk_ms: int = int(settings.chunk_ms)
        self.blocksize: int = max(1, int(self.sample_rate * self.chunk_ms / 1000))
        self._loop = loop
        self._queue: asyncio.Queue[bytes] | None = None
        self._queue_max = max(10, int(1000 / self.chunk_ms))  # ~1 s bufer
        self._stream: Any = None
        self._running = False

        # Holatlar
        self.muted: bool = False
        self.ptt_mode: bool = False
        self.ptt_pressed: bool = False
        self.sensitivity: float = 0.5
        self._threshold: float = float(getattr(settings, "vad_threshold", 0.02))
        self.speaking: bool = False  # gate ochiq (UI holati uchun)
        self._gate_last_open = 0.0
        self._gate_hold_s = 0.6
        self.device_index: int | None = resolve_device(getattr(settings, "input_device", None))

        self._last_level_ts = 0.0
        self._level_interval = 1.0 / LEVEL_PUBLISH_HZ
        self._dropped = 0
        self._echo_suppressed = 0

        # Upstream pauza: sessiya yo'q paytda (ulanishdan oldin / qayta ulanishda) chunklar navbatga qo'yilmaydi.
        # Gemini mijozi `pause_upstream()` / `resume_upstream()` orqali boshqaradi.
        self.upstream_paused: bool = False
        self.echo_guard: bool = bool(getattr(settings, "echo_guard", True))
        self.echo_barge_factor: float = float(getattr(settings, "echo_barge_factor", 3.0))

        # Gemini mijozi uchun ilgaklar (PTT rejimi o'zgarganda VAD konfiguratsiyasi, bosish → activity signallari)
        self.on_ptt_mode_change: Callable[[bool], None] | None = None
        self.on_ptt_press: Callable[[bool], None] | None = None

        self.player = AudioPlayer(
            sample_rate=int(settings.output_sample_rate),
            enabled=bool(getattr(settings, "playback_enabled", True)),
            bus=bus,
            prebuffer_ms=int(getattr(settings, "playback_prebuffer_ms", 0)),
        )

    # --- hayot sikli -------------------------------------------------
    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.stop()

    def start(self) -> None:
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=self._queue_max)
        self._running = True
        self._open_stream()
        self.player.start()
        self.publish_settings()
        self.publish_devices()

    def stop(self) -> None:
        self._running = False
        self._close_stream()
        self.player.stop()

    def _open_stream(self) -> None:
        self._close_stream()
        try:
            s = _require_sd()
            self._stream = s.RawInputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self.blocksize,
                device=self.device_index,
                callback=self._callback,
            )
            self._stream.start()
            log.info(
                "Mikrofon oqimi ochildi: %d Hz, %d ms chunk, qurilma=%s",
                self.sample_rate, self.chunk_ms, self.current_device_name(),
            )
        except Exception as e:  # noqa: BLE001
            self._stream = None
            msg = f"Mikrofon ochilmadi: {e}. {MIC_PERMISSION_HINT}"
            log.error(msg)
            self.bus.publish("LOG", {"level": "error", "message": msg})

    def _close_stream(self) -> None:
        st, self._stream = self._stream, None
        if st is not None:
            try:
                st.stop()
                st.close()
            except Exception as e:  # noqa: BLE001
                log.debug("Oqimni yopishda xato: %s", e)

    @property
    def is_open(self) -> bool:
        return self._stream is not None

    # --- PortAudio callback (alohida thread) ---------------------------
    def _callback(self, indata: Any, frames: int, time_info: Any, status: Any) -> None:
        if status:
            log.debug("Mikrofon status: %s", status)
        chunk = bytes(indata)
        self._process_chunk(chunk)

    def _process_chunk(self, chunk: bytes) -> bool:
        """Callback thread'da: darajani hisoblaydi, gate'ni yangilaydi, navbatga qo'yadi.

        True qaytarsa chunk upstream'ga yuborildi (test uchun qulay)."""
        now = time.monotonic()
        rms, db = compute_rms(chunk)

        # Gate (faqat UI holati uchun)
        if gate_open(rms, self._threshold):
            self._gate_last_open = now
            if not self.speaking:
                self.speaking = True
                self._on_gate_change(True)
        elif self.speaking and now - self._gate_last_open > self._gate_hold_s:
            self.speaking = False
            self._on_gate_change(False)

        # Daraja — throttling
        if now - self._last_level_ts >= self._level_interval:
            self._last_level_ts = now
            self.bus.publish("AUDIO_LEVEL", {"rms": round(rms, 4), "db": round(db, 1)})

        if not self._running or self.upstream_paused:
            return False
        if not should_forward(self.muted, self.ptt_mode, self.ptt_pressed):
            return False
        loop, q = self._loop, self._queue
        if loop is None or q is None or loop.is_closed():
            return False
        if not echo_gate(rms, self._threshold, self.player.is_playing, self.echo_guard, self.echo_barge_factor):
            # Yordamchi gapiryapti, foydalanuvchi jim — oqim uzluksiz qolsin, lekin sukunat ketsin
            self._echo_suppressed += 1
            chunk = b"\x00" * len(chunk)
        loop.call_soon_threadsafe(self._enqueue, chunk)
        return True

    def _enqueue(self, chunk: bytes | str) -> None:
        q = self._queue
        if q is None:
            return
        if q.full():
            try:
                q.get_nowait()  # eng eskisini tashlaymiz — latency yig'ilmasin
                self._dropped += 1
            except asyncio.QueueEmpty:
                pass
        try:
            q.put_nowait(chunk)
        except asyncio.QueueFull:
            pass

    def _on_gate_change(self, is_open: bool) -> None:
        # Faqat idle<->listening o'tishlarini boshqaramiz; speaking/tool holatlariga tegmaymiz.
        if is_open and self.bus.state == "idle" and should_forward(self.muted, self.ptt_mode, self.ptt_pressed):
            self.bus.set_state("listening")
        elif not is_open and self.bus.state == "listening":
            self.bus.set_state("idle")

    def push_marker(self, marker: str) -> None:
        """Navbatga boshqaruv markeri (MARK_ACTIVITY_START/END) qo'yadi — audio bilan tartibda ketadi."""
        if self._queue is None:
            return
        loop = self._loop
        if loop is not None and not loop.is_closed():
            # call_soon — audio thread'dan call_soon_threadsafe bilan kelgan chunklar bilan bir navbatda (FIFO)
            loop.call_soon(self._enqueue, marker)
        else:
            self._enqueue(marker)

    # --- iste'mol ------------------------------------------------------
    async def frames(self) -> AsyncIterator[bytes | str]:
        """Yuboriladigan PCM chunklar yoki `str` markerlar (cheksiz; `stop()` da tugaydi)."""
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=self._queue_max)
        q = self._queue
        while self._running or not q.empty():
            try:
                chunk = await asyncio.wait_for(q.get(), timeout=0.5)
            except TimeoutError:
                continue
            yield chunk

    def drain(self) -> int:
        """Navbatdagi eski chunklarni tashlaydi (qayta ulanishda)."""
        n = 0
        if self._queue is not None:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    n += 1
                except asyncio.QueueEmpty:
                    break
        return n

    def pause_upstream(self) -> None:
        """Sessiya yo'q — chunklar navbatga qo'yilmaydi (ulanishdan oldin / uzilganda)."""
        self.upstream_paused = True

    def resume_upstream(self, drain: bool = True) -> int:
        """Sessiya tayyor — eski chunklarni tashlab, oqimni davom ettiradi."""
        n = self.drain() if drain else 0
        self.upstream_paused = False
        return n

    @property
    def dropped(self) -> int:
        return self._dropped

    @property
    def echo_suppressed(self) -> int:
        return self._echo_suppressed

    # --- boshqaruv -----------------------------------------------------
    def set_muted(self, muted: bool) -> None:
        self.muted = bool(muted)
        if self.muted and self.bus.state == "listening":
            self.bus.set_state("idle")
        self.publish_settings()

    def set_ptt_mode(self, enabled: bool) -> None:
        enabled = bool(enabled)
        changed = enabled != self.ptt_mode
        self.ptt_mode = enabled
        if not self.ptt_mode:
            self.ptt_pressed = False
        self.publish_settings()
        if changed and self.on_ptt_mode_change is not None:
            try:
                self.on_ptt_mode_change(self.ptt_mode)
            except Exception as e:  # noqa: BLE001
                log.warning("on_ptt_mode_change xatosi: %s", e)

    def set_ptt_pressed(self, pressed: bool) -> None:
        pressed = bool(pressed)
        changed = pressed != self.ptt_pressed
        self.ptt_pressed = pressed
        if self.ptt_mode:
            if self.ptt_pressed and self.bus.state == "idle":
                self.bus.set_state("listening")
            elif not self.ptt_pressed and self.bus.state == "listening":
                self.bus.set_state("idle")
            if changed and self.on_ptt_press is not None:
                try:
                    self.on_ptt_press(self.ptt_pressed)
                except Exception as e:  # noqa: BLE001
                    log.warning("on_ptt_press xatosi: %s", e)

    def set_sensitivity(self, value: float) -> None:
        self.sensitivity = max(0.0, min(1.0, float(value)))
        base = float(getattr(self.settings, "vad_threshold", 0.02))
        self._threshold = sensitivity_to_threshold(self.sensitivity, base)
        self.publish_settings()

    def set_playback(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled and not self.player.enabled:
            self.player.enabled = True
            self.player.start()
        elif not enabled and self.player.enabled:
            self.player.stop()
            self.player.enabled = False
        self.publish_settings()

    def set_device(self, index: int | str | None) -> None:
        self.device_index = resolve_device(index)
        if self._running:
            self._open_stream()
        self.publish_devices()

    def current_device_name(self) -> str:
        if sd is None:
            return "yo'q"
        try:
            idx = self.device_index if self.device_index is not None else _default_input_index()
            return str(sd.query_devices(idx)["name"])
        except Exception:  # noqa: BLE001
            return "standart"

    def publish_settings(self) -> dict[str, Any]:
        data = dict(self.bus.snapshot.get("SETTINGS") or {})
        data.update(
            {
                "muted": self.muted,
                "ptt": self.ptt_mode,
                "sensitivity": self.sensitivity,
                "playback": self.player.enabled,
            }
        )
        self.bus.publish("SETTINGS", data)
        return data

    def publish_devices(self) -> dict[str, Any]:
        data = {"devices": list_input_devices(), "current": self.device_index}
        self.bus.publish("DEVICES", data)
        return data

    # --- bus buyruqlari ------------------------------------------------
    def register_commands(self) -> None:
        bus = self.bus

        async def _mute(msg: dict) -> dict:
            self.set_muted(bool(msg.get("value", True)))
            return {"muted": self.muted}

        async def _ptt(msg: dict) -> dict:
            self.set_ptt_mode(bool(msg.get("value", False)))
            return {"ptt": self.ptt_mode}

        async def _ptt_press(msg: dict) -> dict:
            self.set_ptt_pressed(bool(msg.get("value", False)))
            return {"ptt_pressed": self.ptt_pressed}

        async def _sensitivity(msg: dict) -> dict:
            self.set_sensitivity(float(msg.get("value", 0.5)))
            return {"sensitivity": self.sensitivity}

        async def _set_device(msg: dict) -> dict:
            self.set_device(msg.get("index"))
            return {"current": self.device_index}

        async def _list_devices(_msg: dict) -> dict:
            return self.publish_devices()

        async def _playback(msg: dict) -> dict:
            self.set_playback(bool(msg.get("value", True)))
            return {"playback": self.player.enabled}

        bus.register_command("mute", _mute)
        bus.register_command("ptt", _ptt)
        bus.register_command("ptt_press", _ptt_press)
        bus.register_command("sensitivity", _sensitivity)
        bus.register_command("set_device", _set_device)
        bus.register_command("list_devices", _list_devices)
        bus.register_command("playback", _playback)
