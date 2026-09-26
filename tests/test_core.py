"""Yadro testlari — real mikrofon va Gemini API'siz."""
from __future__ import annotations

import asyncio
import math
import sys
import types as pytypes
from types import SimpleNamespace
from typing import ClassVar

import numpy as np
import pytest

# --- sounddevice bo'lmasa (CI) — soxta modul -------------------------------
try:
    import sounddevice  # noqa: F401
except Exception:  # noqa: BLE001
    fake = pytypes.ModuleType("sounddevice")
    fake.query_devices = lambda *a, **k: []  # type: ignore[attr-defined]
    fake.default = SimpleNamespace(device=(None, None))  # type: ignore[attr-defined]
    fake.RawInputStream = None  # type: ignore[attr-defined]
    fake.RawOutputStream = None  # type: ignore[attr-defined]
    sys.modules["sounddevice"] = fake

from nexus import audio_streamer as am
from nexus.audio_streamer import (
    AudioPlayer,
    AudioStreamer,
    compute_rms,
    echo_gate,
    sensitivity_to_threshold,
    should_forward,
)
from nexus.events import EventBus
from nexus.gemini_live_client import (
    CONFIG_FALLBACK_ORDER,
    GeminiLiveClient,
    compute_backoff,
    should_drop_resume_handle,
)


# ---------------------------------------------------------------------------
# Yordamchilar
# ---------------------------------------------------------------------------
def make_settings(**over) -> SimpleNamespace:
    base = {
        "gemini_api_key": "test-key",
        "gemini_model": "gemini-test",
        "gemini_voice": "Aoede",
        "input_sample_rate": 16000,
        "output_sample_rate": 24000,
        "chunk_ms": 20,
        "input_device": None,
        "playback_enabled": False,
        "vad_threshold": 0.02,
        "reconnect_base_delay": 1.0,
        "reconnect_max_delay": 30.0,
        "echo_guard": True,
        "echo_barge_factor": 3.0,
        "playback_prebuffer_ms": 0,
        "vad_start_sensitivity": "LOW",
        "vad_end_sensitivity": "HIGH",
        "vad_prefix_ms": 150,
        "vad_silence_ms": 500,
        "transcription_language_list": ["uz-UZ", "ru-RU", "en-US"],
        "session_resumption": True,
        "context_compression": True,
        "wake_name": "Nexus",
        "wake_mode": "always",
        "wake_follow_up_s": 25.0,
    }
    base.update(over)
    return SimpleNamespace(**base)


def sine_pcm(amplitude: float, n: int = 320, freq: float = 440.0, sr: int = 16000) -> bytes:
    t = np.arange(n) / sr
    s = (np.sin(2 * math.pi * freq * t) * amplitude * 32767).astype(np.int16)
    return s.tobytes()


class FakeStream:
    """RawInputStream/RawOutputStream o'rnini bosuvchi."""

    instances: ClassVar[list[FakeStream]] = []

    def __init__(self, **kw):
        self.kw = kw
        self.started = False
        self.closed = False
        FakeStream.instances.append(self)

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def close(self):
        self.closed = True


@pytest.fixture
def fake_sd(monkeypatch):
    FakeStream.instances.clear()
    sd = SimpleNamespace(
        RawInputStream=FakeStream,
        RawOutputStream=FakeStream,
        query_devices=lambda idx=None: (
            [
                {"name": "Mic A", "max_input_channels": 1},
                {"name": "Speaker", "max_input_channels": 0},
                {"name": "Mic B", "max_input_channels": 2},
            ]
            if idx is None
            else {"name": ["Mic A", "Speaker", "Mic B"][idx]}
        ),
        default=SimpleNamespace(device=(0, 1)),
    )
    monkeypatch.setattr(am, "sd", sd)
    return sd


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------
async def test_eventbus_publish_reaches_subscriber():
    bus = EventBus()
    bus.bind_loop()
    q = bus.subscribe()
    bus.publish("LOG", {"level": "info", "message": "salom"})
    ev = await asyncio.wait_for(q.get(), 1)
    assert ev["type"] == "LOG"
    assert ev["data"]["message"] == "salom"
    assert bus.history()[-1] is ev


async def test_eventbus_publish_from_thread():
    bus = EventBus()
    bus.bind_loop()
    q = bus.subscribe()
    await asyncio.to_thread(bus.publish, "AUDIO_LEVEL", {"rms": 0.1, "db": -20})
    ev = await asyncio.wait_for(q.get(), 1)
    assert ev["type"] == "AUDIO_LEVEL"


async def test_eventbus_state_and_snapshot():
    bus = EventBus()
    bus.bind_loop()
    bus.set_state("listening")
    assert bus.state == "listening"
    bus.publish("SETTINGS", {"muted": True})
    assert bus.snapshot["SETTINGS"]["muted"] is True
    with pytest.raises(ValueError):
        bus.set_state("nimadir")


# ---------------------------------------------------------------------------
# RMS
# ---------------------------------------------------------------------------
def test_compute_rms_silence():
    rms, db = compute_rms(b"\x00" * 640)
    assert rms == 0.0
    assert db == -60.0


def test_compute_rms_empty():
    assert compute_rms(b"") == (0.0, -60.0)
    assert compute_rms(b"\x01") == (0.0, -60.0)


def test_compute_rms_sine():
    rms, db = compute_rms(sine_pcm(0.5))
    # sinus RMS = A/sqrt(2)
    assert abs(rms - 0.5 / math.sqrt(2)) < 0.01
    assert -10.0 < db < -8.0


def test_compute_rms_full_scale_clamped():
    pcm = (np.full(320, 32767, dtype=np.int16)).tobytes()
    rms, db = compute_rms(pcm)
    assert 0.99 < rms <= 1.0
    assert -0.1 <= db <= 0.0


# ---------------------------------------------------------------------------
# Gating
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "muted,ptt,pressed,expected",
    [
        (False, False, False, True),
        (True, False, False, False),
        (False, True, False, False),
        (False, True, True, True),
        (True, True, True, False),
    ],
)
def test_should_forward(muted, ptt, pressed, expected):
    assert should_forward(muted, ptt, pressed) is expected


def test_sensitivity_threshold_monotonic():
    base = 0.02
    assert sensitivity_to_threshold(0.5, base) == pytest.approx(base)
    assert sensitivity_to_threshold(0.0, base) > sensitivity_to_threshold(1.0, base)
    assert sensitivity_to_threshold(1.5, base) == sensitivity_to_threshold(1.0, base)


# ---------------------------------------------------------------------------
# AudioStreamer (soxta sounddevice)
# ---------------------------------------------------------------------------
async def test_streamer_forwards_and_gates(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    st = AudioStreamer(bus, make_settings())
    st.start()
    assert st.is_open

    loud = sine_pcm(0.5)
    assert st._process_chunk(loud) is True
    await asyncio.sleep(0)  # call_soon_threadsafe ishlashi uchun
    frames = st.frames()
    chunk = await asyncio.wait_for(frames.__anext__(), 1)
    assert chunk == loud
    assert st.speaking is True
    assert bus.state == "listening"

    st.set_muted(True)
    assert st._process_chunk(loud) is False
    assert bus.state == "idle"

    st.set_muted(False)
    st.set_ptt_mode(True)
    assert st._process_chunk(loud) is False
    st.set_ptt_pressed(True)
    assert st._process_chunk(loud) is True
    st.stop()
    assert not st.is_open


async def test_streamer_queue_drops_oldest(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    st = AudioStreamer(bus, make_settings(chunk_ms=100))  # queue_max = 10
    st.start()
    for i in range(15):
        st._enqueue(bytes([i]) * 2)
    assert st._queue.qsize() == 10
    assert st._queue.get_nowait() == bytes([5]) * 2
    assert st._dropped == 5
    st.stop()


async def test_streamer_audio_level_throttled(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    q = bus.subscribe()
    st = AudioStreamer(bus, make_settings())
    st.start()
    for _ in range(10):
        st._process_chunk(b"\x00" * 640)
    levels = []
    while not q.empty():
        ev = q.get_nowait()
        if ev["type"] == "AUDIO_LEVEL":
            levels.append(ev)
    assert len(levels) == 1  # 10 chunk, lekin 50ms ichida faqat 1 ta
    st.stop()


async def test_streamer_devices_and_set_device(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    st = AudioStreamer(bus, make_settings(input_device="Mic B"))
    assert st.device_index == 2
    st.start()
    devs = st.publish_devices()
    assert [d["index"] for d in devs["devices"]] == [0, 2]
    assert devs["devices"][0]["default"] is True
    before = len(FakeStream.instances)
    st.set_device(0)
    assert st.device_index == 0
    assert len(FakeStream.instances) == before + 1  # oqim qayta ochildi
    assert st.current_device_name() == "Mic A"
    st.stop()


async def test_streamer_open_failure_publishes_hint(fake_sd, monkeypatch):
    def boom(**kw):
        raise OSError("PortAudio error -9986")

    monkeypatch.setattr(fake_sd, "RawInputStream", boom)
    bus = EventBus()
    bus.bind_loop()
    q = bus.subscribe()
    st = AudioStreamer(bus, make_settings())
    st.start()
    assert not st.is_open
    msgs = [q.get_nowait() for _ in range(q.qsize())]
    logs = [m for m in msgs if m["type"] == "LOG"]
    assert logs and "Mikrofon" in logs[0]["data"]["message"]
    st.stop()


async def test_bus_commands(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    st = AudioStreamer(bus, make_settings())
    st.register_commands()
    st.start()
    r = await bus.dispatch_command({"cmd": "mute", "value": True})
    assert r == {"ok": True, "cmd": "mute", "muted": True}
    r = await bus.dispatch_command({"cmd": "sensitivity", "value": 0.9})
    assert r["sensitivity"] == 0.9
    r = await bus.dispatch_command({"cmd": "list_devices"})
    assert r["ok"] and len(r["devices"]) == 2
    r = await bus.dispatch_command({"cmd": "yoq"})
    assert r["ok"] is False
    st.stop()


# ---------------------------------------------------------------------------
# AudioPlayer
# ---------------------------------------------------------------------------
def test_player_callback_and_clear():
    p = AudioPlayer(enabled=False)
    p.enqueue(b"\x01\x02" * 100)  # 200 bayt
    p.enqueue(b"\x03\x04" * 100)
    assert p.is_playing
    out = bytearray(240)  # 120 frame
    p._callback(out, 120, None, None)
    assert bytes(out[:200]) == b"\x01\x02" * 100
    assert bytes(out[200:240]) == b"\x03\x04" * 20
    assert p.pending_bytes() == 160
    assert p.clear() == 0  # leftover'da edi, navbat bo'sh
    assert p.pending_bytes() == 0
    out2 = bytearray(240)
    p._callback(out2, 120, None, None)
    assert bytes(out2) == b"\x00" * 240
    assert p.is_playing is False


# ---------------------------------------------------------------------------
# Backoff
# ---------------------------------------------------------------------------
def test_compute_backoff():
    assert compute_backoff(0, 1.0, 30.0, jitter=0) == 1.0
    assert compute_backoff(3, 1.0, 30.0, jitter=0) == 8.0
    assert compute_backoff(10, 1.0, 30.0, jitter=0) == 30.0
    assert compute_backoff(2, 1.0, 30.0, jitter=0.5) == 4.5
    assert compute_backoff(-1, 1.0, 30.0, jitter=0) == 1.0
    for n in range(8):
        d = compute_backoff(n, 1.0, 30.0)
        assert 0 <= d <= 30.0


# ---------------------------------------------------------------------------
# GeminiLiveClient — tool_call
# ---------------------------------------------------------------------------
class FakeSession:
    """`turns` — har bir receive() iteratsiyasida beriladigan xabarlar ro'yxati (bo'sh = uzilish)."""

    def __init__(self, turns: list[list] | None = None):
        self.tool_responses = []
        self.client_content = []
        self.realtime = []
        self.closed = False
        self.turns = list(turns or [])
        self.receive_calls = 0

    async def receive(self):
        self.receive_calls += 1
        if not self.turns:
            return
        turn = self.turns.pop(0)
        for m in turn:
            await asyncio.sleep(0)
            yield m

    async def send_realtime_input(self, **kw):
        self.realtime.append(kw)

    async def send_tool_response(self, *, function_responses):
        self.tool_responses.append(list(function_responses))

    async def send_client_content(self, *, turns, turn_complete=True):
        self.client_content.append((turns, turn_complete))

    async def close(self):
        self.closed = True


class FakeRegistry:
    def __init__(self):
        self.calls = []
        self.cancelled = 0
        self.turns = 0
        self.utterances: list[tuple[str, float]] = []
        self.extra: dict = {}  # execute natijasiga qo'shiladigan maydonlar (note/next_step)

    def new_turn(self):
        self.turns += 1

    def note_utterance(self, text, ts=None):
        self.utterances.append((text, ts))

    def declarations(self):
        return [{"name": "open_app", "description": "x", "parameters": {"type": "OBJECT", "properties": {}}}]

    async def execute(self, name, args):
        self.calls.append((name, args))
        if name == "fail":
            raise RuntimeError("portlash")
        await asyncio.sleep(0.01)
        return {"ok": True, "output": f"{name} bajarildi", "duration_ms": 10, "error": None, **self.extra}

    def cancel_all(self):
        self.cancelled += 1
        return 3


class FakeAudio:
    def __init__(self, ptt_mode: bool = False):
        self.player = AudioPlayer(enabled=False)
        self.ptt_mode = ptt_mode
        self.upstream_paused = False
        self.dropped = 0
        self.markers: list[str] = []
        self.items: list = []  # frames() orqali beriladigan elementlar
        self.on_ptt_mode_change = None
        self.on_ptt_press = None

    def drain(self):
        return 0

    def pause_upstream(self):
        self.upstream_paused = True

    def resume_upstream(self, drain=True):
        self.upstream_paused = False
        return 0

    def push_marker(self, marker: str):
        self.markers.append(marker)

    async def frames(self):
        for it in self.items:
            yield it
        await asyncio.sleep(10)  # keyin "cheksiz" kutamiz


def make_client() -> tuple[GeminiLiveClient, EventBus, FakeRegistry, FakeAudio]:
    bus = EventBus()
    bus.bind_loop()
    reg = FakeRegistry()
    audio = FakeAudio()
    client = GeminiLiveClient(bus, make_settings(), reg, audio)
    return client, bus, reg, audio


async def test_handle_tool_call_sends_responses():
    client, bus, reg, _ = make_client()
    session = FakeSession()
    tool_call = SimpleNamespace(
        function_calls=[
            SimpleNamespace(id="c1", name="open_app", args={"name": "Safari"}),
            SimpleNamespace(id="c2", name="fail", args={}),
        ]
    )
    results = await client._handle_tool_call(session, tool_call)
    assert reg.calls == [("open_app", {"name": "Safari"}), ("fail", {})]
    assert results[0]["response"] == {"ok": True, "output": "open_app bajarildi"}
    assert results[1]["response"]["ok"] is False
    assert "portlash" in results[1]["response"]["error"]
    assert len(session.tool_responses) == 1
    frs = session.tool_responses[0]
    assert [fr.id for fr in frs] == ["c1", "c2"]
    assert frs[0].name == "open_app"
    assert frs[0].response["output"] == "open_app bajarildi"
    assert bus.state == "processing"


async def test_handle_message_tool_call_does_not_block():
    client, bus, _reg, _ = make_client()
    session = FakeSession()
    msg = SimpleNamespace(
        server_content=None,
        tool_call=SimpleNamespace(function_calls=[SimpleNamespace(id="a", name="slow", args={})]),
        tool_call_cancellation=None,
        go_away=None,
    )
    await client._handle_message(session, msg)
    assert bus.state == "tool_executing"
    assert len(client._tool_tasks) == 1
    assert session.tool_responses == []  # hali bajarilmoqda
    await asyncio.gather(*client._tool_tasks)
    assert len(session.tool_responses) == 1


async def test_handle_message_cancellation_and_go_away():
    client, _bus, reg, _ = make_client()
    session = FakeSession()
    client._session = session
    msg = SimpleNamespace(
        server_content=None,
        tool_call=None,
        tool_call_cancellation=SimpleNamespace(ids=["a"]),
        go_away=SimpleNamespace(time_left="10s"),
        session_resumption_update=None,
    )
    await client._handle_message(session, msg)
    assert reg.cancelled == 1
    assert client._reconnect_requested is True
    assert client._go_away_pending is True  # receive sikli yumshoq chiqadi, run() resume handle bilan qayta uladi


async def test_server_content_audio_transcript_interrupt():
    client, bus, _reg, audio = make_client()
    q = bus.subscribe()
    # Foydalanuvchi transkripti
    client._handle_server_content(
        SimpleNamespace(
            interrupted=None, input_transcription=SimpleNamespace(text="Safari", finished=False),
            output_transcription=None, model_turn=None, turn_complete=None,
        )
    )
    client._handle_server_content(
        SimpleNamespace(
            interrupted=None, input_transcription=SimpleNamespace(text=" ni och", finished=True),
            output_transcription=None, model_turn=None, turn_complete=None,
        )
    )
    assert bus.state == "processing"
    # Model audio
    part = SimpleNamespace(inline_data=SimpleNamespace(data=b"\x00\x01" * 50), text=None)
    client._handle_server_content(
        SimpleNamespace(
            interrupted=None, input_transcription=None,
            output_transcription=SimpleNamespace(text="Ochyapman"),
            model_turn=SimpleNamespace(parts=[part]), turn_complete=None,
        )
    )
    assert bus.state == "speaking"
    assert audio.player.pending_bytes() == 100
    assert client.last_latency_ms is not None
    # Interrupt
    client._handle_server_content(
        SimpleNamespace(
            interrupted=True, input_transcription=None, output_transcription=None,
            model_turn=None, turn_complete=None,
        )
    )
    assert audio.player.pending_bytes() == 0
    assert bus.state == "listening"
    # turn_complete
    client._handle_server_content(
        SimpleNamespace(
            interrupted=None, input_transcription=None, output_transcription=None,
            model_turn=None, turn_complete=True,
        )
    )
    assert bus.state == "idle"

    events = []
    while not q.empty():
        events.append(q.get_nowait())
    tr = [e["data"] for e in events if e["type"] == "TRANSCRIPT"]
    finals_user = [t for t in tr if t["role"] == "user" and t["final"]]
    assert finals_user == [{"role": "user", "text": "Safari ni och", "final": True}]
    finals_asst = [t for t in tr if t["role"] == "assistant" and t["final"]]
    assert finals_asst[0]["text"] == "Ochyapman"
    metrics = [e["data"] for e in events if e["type"] == "METRICS"]
    assert metrics and "latency_ms" in metrics[-1]


async def test_send_text_and_text_command():
    client, bus, _reg, _ = make_client()
    assert await client.send_text("salom") is False  # sessiya yo'q
    session = FakeSession()
    client._session = session
    r = await bus.dispatch_command({"cmd": "text", "value": "Safari ni och"})
    assert r["sent"] is True
    turns, complete = session.client_content[0]
    assert turns.role == "user" and turns.parts[0].text == "Safari ni och"
    assert complete is True
    assert bus.state == "processing"


async def test_run_requires_api_key():
    from nexus.gemini_live_client import GeminiConfigError

    bus = EventBus()
    bus.bind_loop()
    client = GeminiLiveClient(bus, make_settings(gemini_api_key=""), FakeRegistry(), FakeAudio())
    with pytest.raises(GeminiConfigError) as ei:
        await client.run()
    assert "GEMINI_API_KEY" in str(ei.value)


async def test_build_config_uses_registry_declarations():
    client, *_ = make_client()
    cfg = client._build_config()
    assert cfg.response_modalities == ["AUDIO"]
    assert cfg.tools[0].function_declarations[0].name == "open_app"
    assert cfg.speech_config.voice_config.prebuilt_voice_config.voice_name == "Aoede"
    assert cfg.input_audio_transcription is not None


def _msg(**kw) -> SimpleNamespace:
    base = {
        "server_content": None, "tool_call": None, "tool_call_cancellation": None,
        "go_away": None, "session_resumption_update": None,
    }
    base.update(kw)
    return SimpleNamespace(**base)


def _sc(**kw) -> SimpleNamespace:
    base = {
        "interrupted": None, "input_transcription": None, "output_transcription": None,
        "model_turn": None, "generation_complete": None, "turn_complete": None,
    }
    base.update(kw)
    return SimpleNamespace(**base)


def _audio_part(n: int = 50) -> SimpleNamespace:
    return SimpleNamespace(inline_data=SimpleNamespace(data=b"\x00\x01" * n), text=None)


# ---------------------------------------------------------------------------
# LiveConnectConfig — VAD, til, resumption, compression
# ---------------------------------------------------------------------------
async def test_build_config_vad_language_resumption_compression():
    from google.genai import types

    client, *_ = make_client()
    client._resume_handle = "h-1"
    cfg = client._build_config()
    aad = cfg.realtime_input_config.automatic_activity_detection
    assert aad.disabled is False
    assert aad.start_of_speech_sensitivity == types.StartSensitivity.START_SENSITIVITY_LOW
    assert aad.end_of_speech_sensitivity == types.EndSensitivity.END_SENSITIVITY_HIGH
    assert aad.prefix_padding_ms == 150 and aad.silence_duration_ms == 500
    assert cfg.input_audio_transcription.language_codes == ["uz-UZ", "ru-RU", "en-US"]
    assert cfg.session_resumption.handle == "h-1"
    assert cfg.context_window_compression.sliding_window is not None
    assert cfg.media_resolution == types.MediaResolution.MEDIA_RESOLUTION_HIGH
    assert cfg.enable_affective_dialog is None  # 1007 xato — ishlatilmaydi
    assert client._vad_disabled is False


async def test_build_config_ptt_disables_vad_and_optional_fields():
    bus = EventBus()
    bus.bind_loop()
    audio = FakeAudio(ptt_mode=True)
    settings = make_settings(session_resumption=False, context_compression=False, transcription_language_list=[])
    client = GeminiLiveClient(bus, settings, FakeRegistry(), audio)
    cfg = client._build_config()
    assert cfg.realtime_input_config.automatic_activity_detection.disabled is True
    assert client._vad_disabled is True
    assert cfg.session_resumption is None
    assert cfg.context_window_compression is None
    assert cfg.input_audio_transcription.language_codes is None


# ---------------------------------------------------------------------------
# receive() semantikasi va sessiya davomiyligi
# ---------------------------------------------------------------------------
async def test_receive_loop_reenters_until_empty_iteration():
    client, _bus, _reg, audio = make_client()
    turn1 = [
        _msg(session_resumption_update=SimpleNamespace(resumable=True, new_handle="hnd-A")),
        _msg(server_content=_sc(model_turn=SimpleNamespace(parts=[_audio_part()]))),
        _msg(server_content=_sc(turn_complete=True)),
    ]
    turn2 = [
        _msg(session_resumption_update=SimpleNamespace(resumable=False, new_handle="ignored")),
        _msg(server_content=_sc(turn_complete=True)),
    ]
    session = FakeSession(turns=[turn1, turn2])  # 3-iteratsiya bo'sh → uzilish
    await asyncio.wait_for(client._receive(session), 2)
    assert session.receive_calls == 3  # ikki navbat + bo'sh (haqiqiy uzilish)
    assert client._resume_handle == "hnd-A"  # resumable=False bo'lgani saqlanmadi
    assert audio.player.pending_bytes() == 100


async def test_receive_loop_exits_on_go_away_softly():
    client, _bus, _reg, _ = make_client()
    turn1 = [_msg(go_away=SimpleNamespace(time_left="30s")), _msg(server_content=_sc(turn_complete=True))]
    session = FakeSession(turns=[turn1, [_msg(server_content=_sc(turn_complete=True))]])
    await asyncio.wait_for(client._receive(session), 2)
    assert session.receive_calls == 1  # go_away dan keyin darhol chiqdi
    assert client._reconnect_requested and client._go_away_pending
    assert session.closed is False  # soketni o'zimiz yopmaymiz — kontekst chiqishida yopiladi


def test_should_drop_resume_handle():
    assert should_drop_resume_handle(1.0, "h") is True
    assert should_drop_resume_handle(10.0, "h") is False
    assert should_drop_resume_handle(1.0, None) is False
    assert should_drop_resume_handle(None, "h") is False


class FakeLiveConnect:
    """client.aio.live.connect o'rnini bosuvchi: har chaqiruvda navbatdagi FakeSession."""

    def __init__(self, sessions: list[FakeSession]):
        self.sessions = sessions
        self.configs = []

    def connect(self, *, model, config):
        self.configs.append(config)
        sess = self.sessions.pop(0)
        outer = self

        class _Ctx:
            async def __aenter__(self_inner):
                if sess is None:
                    raise ConnectionError("ulanmadi")
                return sess

            async def __aexit__(self_inner, *exc):
                sess.closed = True
                return False

        _ = outer
        return _Ctx()


async def test_run_reconnects_with_resume_handle_and_counts(monkeypatch):
    import google.genai as genai_mod

    from nexus import gemini_live_client as glc

    monkeypatch.setattr(glc, "SHORT_SESSION_S", 0.0)  # testda sessiyalar bir zumda tugaydi — handle saqlansin
    client, bus, _reg, audio = make_client()
    client.settings.reconnect_base_delay = 0.01
    client.settings.reconnect_max_delay = 0.02
    s1 = FakeSession(turns=[[
        _msg(session_resumption_update=SimpleNamespace(resumable=True, new_handle="H1")),
        _msg(server_content=_sc(turn_complete=True)),
    ]])  # keyin bo'sh → uzilish
    s2 = FakeSession(turns=[[_msg(go_away=SimpleNamespace(time_left="1s"))]])
    s3 = FakeSession(turns=[])
    live = FakeLiveConnect([s1, s2, s3])
    monkeypatch.setattr(
        genai_mod, "Client", lambda api_key: SimpleNamespace(aio=SimpleNamespace(live=live))
    )
    # Uchinchi sessiya tugagach to'xtatamiz
    orig_loop = client._session_loop

    async def _loop(session):
        await orig_loop(session)
        if session is s3:
            client._stop.set()

    monkeypatch.setattr(client, "_session_loop", _loop)
    await asyncio.wait_for(client.run(), 5)

    assert len(live.configs) == 3
    assert live.configs[0].session_resumption.handle is None
    assert live.configs[1].session_resumption.handle == "H1"  # uzilishdan keyin resume handle bilan
    assert live.configs[2].session_resumption.handle == "H1"  # go_away dan keyin ham
    assert client.reconnects == 2
    assert bus.snapshot["METRICS"]["reconnects"] == 2
    assert s1.closed and s2.closed and s3.closed
    assert audio.upstream_paused is True  # to'xtaganda mikrofon upstream'i pauzada
    assert bus.snapshot["CONNECTION"]["gemini"] == "disconnected"


async def test_run_drops_resume_handle_after_short_session(monkeypatch):
    import google.genai as genai_mod

    client, _bus, _reg, _audio = make_client()
    client.settings.reconnect_base_delay = 0.01
    client.settings.reconnect_max_delay = 0.02
    s1 = FakeSession(turns=[[
        _msg(session_resumption_update=SimpleNamespace(resumable=True, new_handle="H1")),
        _msg(server_content=_sc(turn_complete=True)),
    ]])
    s2 = FakeSession(turns=[])
    live = FakeLiveConnect([s1, s2])
    monkeypatch.setattr(
        genai_mod, "Client", lambda api_key: SimpleNamespace(aio=SimpleNamespace(live=live))
    )
    orig_loop = client._session_loop

    async def _loop(session):
        await orig_loop(session)
        if session is s2:
            client._stop.set()

    monkeypatch.setattr(client, "_session_loop", _loop)
    await asyncio.wait_for(client.run(), 5)
    assert len(live.configs) == 2
    # 1-sessiya 5 s dan kam yashadi → handle yaroqsiz deb tashlandi
    assert live.configs[1].session_resumption.handle is None
    assert client._resume_handle is None


async def test_send_audio_forwards_chunks_and_ptt_markers():
    from google.genai import types

    client, _bus, _reg, audio = make_client()
    client._vad_disabled = True
    audio.items = ["activity_start", b"\x01\x02", "activity_end"]
    session = FakeSession()
    task = asyncio.create_task(client._send_audio(session))
    await asyncio.sleep(0.05)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    assert isinstance(session.realtime[0]["activity_start"], types.ActivityStart)
    assert session.realtime[1]["audio"].data == b"\x01\x02"
    assert session.realtime[1]["audio"].mime_type == "audio/pcm;rate=16000"
    assert isinstance(session.realtime[2]["activity_end"], types.ActivityEnd)

    # VAD yoqiq bo'lsa markerlar yuborilmaydi
    client._vad_disabled = False
    session2 = FakeSession()
    task = asyncio.create_task(client._send_audio(session2))
    await asyncio.sleep(0.05)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    assert [list(k) for k in session2.realtime] == [["audio"]]


async def test_send_audio_error_is_logged_and_raised():
    client, bus, _reg, audio = make_client()
    q = bus.subscribe()
    audio.items = [b"\x01\x02"]

    class Boom(FakeSession):
        async def send_realtime_input(self, **kw):
            raise OSError("soket yopiq")

    with pytest.raises(OSError):
        await client._send_audio(Boom())
    logs = [q.get_nowait() for _ in range(q.qsize())]
    assert any(e["type"] == "LOG" and "Audio yuborilmadi" in e["data"]["message"] for e in logs)


async def test_ptt_hooks_request_reconnect_and_push_markers():
    client, _bus, _reg, audio = make_client()
    assert audio.on_ptt_mode_change is not None and audio.on_ptt_press is not None
    session = FakeSession()
    client._session = session
    client._vad_disabled = False
    audio.on_ptt_mode_change(True)  # PTT yoqildi — VAD konfiguratsiyasi o'zgaradi → qayta ulanish
    assert client._reconnect_requested is True
    await asyncio.sleep(0)
    assert session.closed is True
    audio.on_ptt_press(True)
    assert audio.markers == []  # joriy sessiyada VAD yoqiq — marker yo'q
    client._vad_disabled = True
    audio.on_ptt_press(True)
    audio.on_ptt_press(False)
    assert audio.markers == ["activity_start", "activity_end"]


# ---------------------------------------------------------------------------
# AudioPlayer — prebuffer / play_out / is_playing
# ---------------------------------------------------------------------------
def test_player_prebuffer_and_play_out():
    p = AudioPlayer(sample_rate=1000, enabled=False, prebuffer_ms=100)  # 200 bayt prebuffer
    p.enqueue(b"\x01\x02" * 50)  # 100 bayt — hali armed emas
    assert p.armed is False
    assert p.is_playing is True  # navbatda audio bor (echo guard uchun)
    out = bytearray(100)
    p._callback(out, 50, None, None)
    assert bytes(out) == b"\x00" * 100  # prebuffer to'lmagan — sukunat
    assert p.pending_bytes() == 100
    p.play_out()  # generation_complete
    assert p.armed is True
    p._callback(out, 50, None, None)
    assert bytes(out) == b"\x01\x02" * 50
    assert p.pending_bytes() == 0
    assert p.armed is False  # bo'shadi — keyingi javob yana prebuffer bilan
    assert p.chunks_played == 1

    p.enqueue(b"\x03\x04" * 100)  # 200 bayt — prebuffer to'ldi
    assert p.armed is True
    p.clear()
    assert p.armed is False and p.pending_bytes() == 0 and p.is_playing is False


def test_player_is_playing_tail(monkeypatch):
    p = AudioPlayer(sample_rate=1000, enabled=False, prebuffer_ms=0)
    t = [100.0]
    monkeypatch.setattr(am.time, "monotonic", lambda: t[0])
    p.enqueue(b"\x01\x02" * 50)
    out = bytearray(100)
    p._callback(out, 50, None, None)
    assert p.pending_bytes() == 0
    assert p.is_playing is True  # dum (tail) — karnaydan hali chiqyapti
    t[0] += 0.5
    assert p.is_playing is False


# ---------------------------------------------------------------------------
# Echo guard
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "rms,playing,guard,expected",
    [
        (0.01, False, True, True),   # ijro yo'q — hamma narsa o'tadi
        (0.01, True, False, True),   # guard o'chiq
        (0.03, True, True, False),   # ijro paytida past RMS — echo, bostiriladi
        (0.07, True, True, True),    # ijro paytida baland RMS (>= 0.02*3) — barge-in
    ],
)
def test_echo_gate(rms, playing, guard, expected):
    assert echo_gate(rms, 0.02, playing, guard, factor=3.0) is expected


async def test_streamer_echo_guard_sends_silence_and_upstream_pause(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    st = AudioStreamer(bus, make_settings())
    st.start()
    st.player.enqueue(b"\x01\x02" * 100)  # "yordamchi gapiryapti"
    quiet = sine_pcm(0.03)
    assert st._process_chunk(quiet) is True  # oqim uzluksiz — lekin sukunat ketadi
    await asyncio.sleep(0)
    assert st._queue.get_nowait() == b"\x00" * len(quiet)
    assert st.echo_suppressed == 1
    loud = sine_pcm(0.5)
    assert st._process_chunk(loud) is True
    await asyncio.sleep(0)
    assert st._queue.empty()  # bitta cho'qqi — hali barge-in emas, ushlab turiladi
    for _ in range(st._barge.need - 1):
        st._process_chunk(loud)
    await asyncio.sleep(0)
    items = [st._queue.get_nowait() for _ in range(st._queue.qsize())]
    assert items == [loud] * st._barge.need  # uzluksiz gap — barge-in, asl chunklar (boshi yo'qolmagan)
    st.player.clear()

    st.pause_upstream()
    assert st._process_chunk(loud) is False
    st.resume_upstream()
    assert st._process_chunk(loud) is True
    st.stop()


async def test_streamer_push_marker_keeps_order(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    st = AudioStreamer(bus, make_settings())
    st.start()
    st.set_ptt_mode(True)
    st.set_ptt_pressed(True)
    st._process_chunk(sine_pcm(0.5))
    st.push_marker("activity_end")
    await asyncio.sleep(0)
    items = [st._queue.get_nowait() for _ in range(st._queue.qsize())]
    assert isinstance(items[0], bytes) and items[1] == "activity_end"
    st.stop()


async def test_streamer_settings_merge_snapshot(fake_sd):
    bus = EventBus()
    bus.bind_loop()
    bus.publish("SETTINGS", {"wake_mode": "name", "name": "Luna"})
    st = AudioStreamer(bus, make_settings())
    data = st.publish_settings()
    assert data["wake_mode"] == "name" and data["muted"] is False


# ---------------------------------------------------------------------------
# interrupted → tool cancel, generation_complete → play_out
# ---------------------------------------------------------------------------
async def test_interrupted_cancels_tools_and_generation_complete_plays_out():
    client, bus, reg, audio = make_client()
    audio.player = AudioPlayer(sample_rate=1000, enabled=False, prebuffer_ms=100)
    client._handle_server_content(_sc(model_turn=SimpleNamespace(parts=[_audio_part(10)])))
    assert audio.player.armed is False
    client._handle_server_content(_sc(generation_complete=True))
    assert audio.player.armed is True
    client._handle_server_content(_sc(interrupted=True))
    assert audio.player.pending_bytes() == 0
    assert reg.cancelled == 1
    assert bus.state == "listening"


# ---------------------------------------------------------------------------
# Wake — mijoz ichida
# ---------------------------------------------------------------------------
async def test_wake_name_mode_suppresses_audio_and_tools():
    bus = EventBus()
    bus.bind_loop()
    reg = FakeRegistry()
    audio = FakeAudio()
    client = GeminiLiveClient(bus, make_settings(wake_mode="name"), reg, audio)
    assert bus.snapshot["SETTINGS"]["wake_mode"] == "name"
    assert bus.snapshot["SETTINGS"]["name"] == "Nexus"
    session = FakeSession()

    # Ismsiz gap → javob audiosi ijro etilmaydi, tool rad etiladi
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="Safarini och", finished=True)))
    assert client._addressed is False
    assert bus.state == "listening"
    client._handle_server_content(_sc(model_turn=SimpleNamespace(parts=[_audio_part()])))
    assert audio.player.pending_bytes() == 0
    assert bus.state != "speaking"
    tc = SimpleNamespace(function_calls=[SimpleNamespace(id="1", name="open_app", args={})])
    results = await client._handle_tool_call(session, tc)
    assert reg.calls == []
    assert results[0]["response"] == {"ok": False, "output": "not addressed"}
    assert session.tool_responses[0][0].response["ok"] is False
    client._handle_server_content(_sc(turn_complete=True))
    assert bus.state == "idle"

    # Ism bilan → oddiy ish
    client._handle_server_content(
        _sc(input_transcription=SimpleNamespace(text="Neksus, Safarini och", finished=True))
    )
    assert client._addressed is True
    assert bus.state == "processing"
    client._handle_server_content(_sc(model_turn=SimpleNamespace(parts=[_audio_part()])))
    assert audio.player.pending_bytes() == 100
    results = await client._handle_tool_call(session, tc)
    assert reg.calls == [("open_app", {})]
    client._handle_server_content(_sc(turn_complete=True))
    # Follow-up oynasi ochiq — ismsiz keyingi gap ham qabul qilinadi
    assert client._addressed is True
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="endi yop", finished=True)))
    assert client._addressed is True


async def test_wake_commands_update_settings():
    client, bus, _reg, _ = make_client()
    r = await bus.dispatch_command({"cmd": "wake_mode", "value": "smart"})
    assert r["ok"] and r["wake_mode"] == "smart"
    r = await bus.dispatch_command({"cmd": "wake_mode", "value": "xato"})
    assert r["ok"] is False
    r = await bus.dispatch_command({"cmd": "set_name", "value": "Luna"})
    assert r["ok"] and client.wake.name == "Luna"
    assert bus.snapshot["SETTINGS"] == {"wake_mode": "smart", "name": "Luna", "dictating": False, "conversation": False}
    r = await bus.dispatch_command({"cmd": "set_name", "value": "  "})
    assert r["ok"] is False


# ---------------------------------------------------------------------------
# Diktovka — mijoz ichida
# ---------------------------------------------------------------------------
async def test_dictation_types_final_pieces_and_stops():
    client, bus, reg, audio = make_client()
    session = FakeSession()
    r = await bus.dispatch_command({"cmd": "dictation", "value": True})
    assert r["dictating"] is True
    assert bus.state == "dictating"
    assert bus.snapshot["SETTINGS"]["dictating"] is True

    # Final bo'lak — darhol teriladi (turn_complete kutilmaydi)
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="Salom dunyo", finished=True)))
    await asyncio.gather(*client._dictation_tasks)
    assert reg.calls == [("type_text", {"text": "Salom dunyo "})]
    assert bus.state == "dictating"

    # Model audiosi ijro etilmaydi, tool rad etiladi
    client._handle_server_content(_sc(model_turn=SimpleNamespace(parts=[_audio_part()])))
    assert audio.player.pending_bytes() == 0
    tc = SimpleNamespace(function_calls=[SimpleNamespace(id="1", name="open_app", args={})])
    results = await client._handle_tool_call(session, tc)
    assert results[0]["response"]["ok"] is False and "dictation" in results[0]["response"]["output"]
    assert len(reg.calls) == 1
    client._handle_server_content(_sc(turn_complete=True))
    assert bus.state == "dictating"

    # turn_complete bilan kelgan bo'lak + to'xtash iborasi
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="oxirgi gap, to'xta", finished=False)))
    client._handle_server_content(_sc(turn_complete=True))
    await asyncio.gather(*client._dictation_tasks)
    assert reg.calls[-1] == ("type_text", {"text": "oxirgi gap "})
    assert client.dictation.active is False
    assert bus.state in ("idle", "listening")  # diktovka holatidan chiqdi
    assert client.dictation.typed_chars == len("Salom dunyo") + len("oxirgi gap")

    # Faqat to'xtash iborasi — hech narsa terilmaydi
    await bus.dispatch_command({"cmd": "dictation", "value": True})
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="bas", finished=True)))
    assert client.dictation.active is False
    assert len(reg.calls) == 2


async def test_dictation_passthrough_stop_tool():
    client, _bus, reg, _ = make_client()
    client.set_dictation(True)
    tc = SimpleNamespace(function_calls=[SimpleNamespace(id="1", name="stop_dictation", args={})])
    results = await client._handle_tool_call(FakeSession(), tc)
    assert reg.calls == [("stop_dictation", {})]
    assert results[0]["response"]["ok"] is True


# ---------------------------------------------------------------------------
# Registry integratsiyasi: new_turn / note_utterance / gate / note+next_step
# ---------------------------------------------------------------------------
async def test_user_turn_notifies_registry():
    client, _bus, reg, _ = make_client()
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="ha, davom et", finished=True)))
    assert reg.turns == 1
    assert len(reg.utterances) == 1
    text, ts = reg.utterances[0]
    assert text == "ha, davom et" and isinstance(ts, float) and ts > 1e9
    # turn_complete da yig'ilgan matn ham
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="yana", finished=False)))
    client._handle_server_content(_sc(turn_complete=True))
    assert reg.turns == 2 and reg.utterances[-1][0] == "yana"
    # UI matni ham
    client._session = FakeSession()
    await client.send_text("Safari ni och")
    assert reg.turns == 3 and reg.utterances[-1][0] == "Safari ni och"
    # Diktovkada "ha" — note_utterance chaqirilmaydi, new_turn chaqiriladi
    client.set_dictation(True)
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="ha", finished=True)))
    await asyncio.gather(*client._dictation_tasks)
    assert reg.turns == 4 and len(reg.utterances) == 3


async def test_user_turn_without_registry_hooks():
    bus = EventBus()
    bus.bind_loop()
    reg = SimpleNamespace(declarations=list, execute=None, cancel_all=lambda: 0)  # hook'lar yo'q
    client = GeminiLiveClient(bus, make_settings(), reg, FakeAudio())
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="salom", finished=True)))
    assert bus.state == "processing"  # xatosiz o'tdi


async def test_interrupted_respects_awaiting_confirmation():
    client, bus, reg, audio = make_client()
    audio.player.enqueue(b"\x01\x02" * 10)
    # 1) Bus holati awaiting_confirmation — holat saqlanadi, tool bekor qilinmaydi
    bus.set_state("awaiting_confirmation")
    client._handle_server_content(_sc(interrupted=True))
    assert audio.player.pending_bytes() == 0
    assert reg.cancelled == 0
    assert bus.state == "awaiting_confirmation"
    # 2) Holat boshqa, lekin gate'da faol so'rov bor — tool bekor qilinmaydi
    bus.set_state("speaking")
    reg.gate = SimpleNamespace(pending=SimpleNamespace(token="t"))
    client._handle_server_content(_sc(interrupted=True))
    assert reg.cancelled == 0
    assert bus.state == "listening"
    # 3) So'rov yo'q — odatdagidek bekor qilinadi
    reg.gate = SimpleNamespace(pending=None)
    client._handle_server_content(_sc(interrupted=True))
    assert reg.cancelled == 1


async def test_tool_response_includes_note_and_next_step():
    client, _bus, reg, _ = make_client()
    reg.extra = {"note": "fayl mavjud edi", "next_step": None}
    session = FakeSession()
    tc = SimpleNamespace(function_calls=[SimpleNamespace(id="1", name="write_file", args={})])
    results = await client._handle_tool_call(session, tc)
    assert results[0]["response"] == {"ok": True, "output": "write_file bajarildi", "note": "fayl mavjud edi"}
    assert session.tool_responses[0][0].response["note"] == "fayl mavjud edi"
    reg.extra = {"next_step": "Endi 'ha' deng"}
    results = await client._handle_tool_call(session, tc)
    assert results[0]["response"]["next_step"] == "Endi 'ha' deng"
    assert "note" not in results[0]["response"]


# ---------------------------------------------------------------------------
# Gemini 3.8: standart model, thinking_config, google_search, config fallback
# ---------------------------------------------------------------------------
def test_config_defaults_gemini38(monkeypatch):
    from nexus.config import Settings  # avval import — load_dotenv() .env dan yuklab qo'ymasin

    for k in ("GEMINI_MODEL", "GEMINI_TEXT_MODEL", "GEMINI_THINKING_LEVEL", "GOOGLE_SEARCH_GROUNDING"):
        monkeypatch.delenv(k, raising=False)
    s = Settings()
    assert s.gemini_model == "gemini-3.8-live"
    assert s.gemini_text_model == "gemini-3.8-flash"
    assert s.thinking_level == ""
    assert s.google_search_grounding is False
    monkeypatch.setenv("GEMINI_THINKING_LEVEL", "Medium")
    assert Settings().thinking_level == "medium"


def test_thinking_level_for():
    from nexus.gemini_live_client import thinking_level_for

    assert thinking_level_for("gemini-3.8-live", "") is None
    assert thinking_level_for("gemini-3.8-live", "low") == "low"
    assert thinking_level_for("gemini-3.8-live-extended-thinking", "") == "high"
    assert thinking_level_for("gemini-3.8-live-extended-thinking", "medium") == "medium"


async def test_build_config_thinking_and_google_search():
    from google.genai import types

    client, *_ = make_client()
    cfg = client._build_config()
    assert cfg.thinking_config is None  # oddiy live model, daraja berilmagan
    assert len(cfg.tools) == 1 and cfg.tools[0].google_search is None

    client.settings.thinking_level = "low"
    client.settings.google_search_grounding = True
    cfg = client._build_config()
    assert cfg.thinking_config.thinking_level == types.ThinkingLevel.LOW
    assert cfg.tools[0].function_declarations[0].name == "open_app"
    assert isinstance(cfg.tools[1].google_search, types.GoogleSearch)

    client.settings.thinking_level = ""
    client.settings.gemini_model = "gemini-3.8-live-extended-thinking"
    assert client._build_config().thinking_config.thinking_level == types.ThinkingLevel.HIGH


def test_is_config_rejection():
    from nexus.gemini_live_client import is_config_rejection

    assert is_config_rejection(RuntimeError("1007 None. Invalid argument: thinking_config")) is True
    assert is_config_rejection(RuntimeError("1007 None. API key not valid.")) is False
    assert is_config_rejection(RuntimeError("1011 internal error")) is False
    # Kvota xatosi (masalan google_search grounding kvotasiz kalitda) ham konfiguratsiya fallback'ini ishga tushiradi
    assert is_config_rejection(RuntimeError("1011 None. You exceeded your current quota, please check")) is True
    e = RuntimeError("closed")
    e.code = 1007  # type: ignore[attr-defined]
    assert is_config_rejection(e) is True


async def test_config_fallback_order_on_1007(monkeypatch):
    import google.genai as genai_mod
    from google.genai import types

    client, bus, _reg, _audio = make_client()
    client.settings.thinking_level = "medium"
    client.settings.reconnect_base_delay = 0.01
    client.settings.reconnect_max_delay = 0.02
    q = bus.subscribe()

    class Rejecting(FakeLiveConnect):
        def connect(self, *, model, config):
            if len(self.configs) < 3:
                self.configs.append(config)

                class _Bad:
                    async def __aenter__(self_inner):
                        raise RuntimeError("1007 None. Invalid argument in setup")

                    async def __aexit__(self_inner, *exc):
                        return False

                return _Bad()
            return super().connect(model=model, config=config)

    s4 = FakeSession(turns=[])
    live = Rejecting([s4])
    monkeypatch.setattr(
        genai_mod, "Client", lambda api_key: SimpleNamespace(aio=SimpleNamespace(live=live))
    )
    orig_loop = client._session_loop

    async def _loop(session):
        await orig_loop(session)
        client._stop.set()

    monkeypatch.setattr(client, "_session_loop", _loop)
    await asyncio.wait_for(client.run(), 5)

    assert len(live.configs) == 4
    c1, c2, c3, c4 = live.configs
    assert c1.thinking_config is not None and c1.input_audio_transcription.language_codes
    assert c1.media_resolution == types.MediaResolution.MEDIA_RESOLUTION_HIGH
    assert c2.thinking_config is None and c2.input_audio_transcription.language_codes  # 1) thinking_config
    assert c3.thinking_config is None and c3.input_audio_transcription.language_codes is None  # 2) language_codes
    assert c3.media_resolution == types.MediaResolution.MEDIA_RESOLUTION_HIGH
    assert c4.media_resolution is None  # 3) media_resolution
    assert client._config_fallback == len(CONFIG_FALLBACK_ORDER)  # google_search (faol emas) o'tkazib yuborilgan
    logs = [e["data"]["message"] for e in [q.get_nowait() for _ in range(q.qsize())] if e["type"] == "LOG"]
    assert sum("rad etdi" in m for m in logs) == 3


async def test_config_fallback_not_applied_for_api_key_error():
    client, *_ = make_client()
    assert client._apply_config_fallback(RuntimeError("1007 None. API key not valid."), None) is False
    assert client._config_fallback == 0
    # Uzoq yashagan sessiya keyin 1007 bilan uzilsa — konfiguratsiya sababi emas
    assert client._apply_config_fallback(RuntimeError("1007 x"), 100.0) is False


async def test_grounding_metadata_publishes_sources():
    client, bus, _reg, _audio = make_client()
    q = bus.subscribe()
    gm = SimpleNamespace(
        grounding_chunks=[
            SimpleNamespace(web=SimpleNamespace(uri="https://a.uz/1", title="A")),
            SimpleNamespace(web=None),
            SimpleNamespace(web=SimpleNamespace(uri="https://b.uz/2", title=None)),
        ]
    )
    client._handle_server_content(_sc(output_transcription=SimpleNamespace(text="Ob-havo 20°"), grounding_metadata=gm))
    client._handle_server_content(_sc(grounding_metadata=gm))  # takror — qayta nashr qilinmaydi
    client._handle_server_content(_sc(turn_complete=True))
    events = [q.get_nowait() for _ in range(q.qsize())]
    logs = [e["data"] for e in events if e["type"] == "LOG" and "Manbalar" in e["data"]["message"]]
    assert len(logs) == 1 and logs[0]["sources"] == ["A — https://a.uz/1", "https://b.uz/2"]
    finals = [e["data"] for e in events if e["type"] == "TRANSCRIPT" and e["data"]["final"]]
    assert finals[-1]["sources"] == ["A — https://a.uz/1", "https://b.uz/2"]
    assert client._sources == []


# ---------------------------------------------------------------------------
# web_answer tool
# ---------------------------------------------------------------------------
async def test_web_answer_parses_interaction(monkeypatch):
    from nexus import web_answer as wa

    captured = {}

    class FakeInteractions:
        async def create(self, **body):
            captured.update(body)
            steps = [
                SimpleNamespace(type="user_input", content=[SimpleNamespace(type="text", text=body["input"])]),
                SimpleNamespace(type="google_search_result", result=[{"title": "Meteo", "uri": "https://m.uz"}]),
                SimpleNamespace(
                    type="model_output",
                    content=[SimpleNamespace(type="text", text="Toshkentda "), SimpleNamespace(type="text", text="+20°C")],
                ),
            ]
            return SimpleNamespace(steps=steps, output_text=None)

    monkeypatch.setattr(wa, "_client_factory", lambda key: SimpleNamespace(aio=SimpleNamespace(interactions=FakeInteractions())))
    monkeypatch.setattr(wa.settings if hasattr(wa, "settings") else __import__("nexus.config").config.settings, "gemini_api_key", "k")
    from nexus.config import settings as cfg

    monkeypatch.setattr(cfg, "gemini_text_model", "gemini-3.8-flash")
    monkeypatch.setattr(cfg, "thinking_level", "")
    res = await wa.web_answer({"question": "Toshkentda ob-havo qanday?"})
    assert res == {"ok": True, "output": "Toshkentda +20°C", "note": "Manbalar: Meteo — https://m.uz"}
    assert captured["model"] == "gemini-3.8-flash"
    assert captured["tools"] == [{"type": "google_search"}]
    assert captured["generation_config"] == {"thinking_level": "medium", "max_output_tokens": 4096}

    # output_text (SDK yig'gan) ustunlik qiladi; uzun javob qisqartiriladi
    long = "so'z " * 800

    class Direct:
        async def create(self, **body):
            return SimpleNamespace(steps=[], output_text=long)

    monkeypatch.setattr(wa, "_client_factory", lambda key: SimpleNamespace(aio=SimpleNamespace(interactions=Direct())))
    res = await wa.web_answer({"question": "x"})
    assert res["ok"] and len(res["output"]) <= wa.MAX_ANSWER_CHARS + 1 and res["output"].endswith("…")


async def test_web_answer_sync_client_and_errors(monkeypatch):
    from nexus import web_answer as wa
    from nexus.config import settings as cfg

    monkeypatch.setattr(cfg, "gemini_api_key", "")
    res = await wa.web_answer({"question": "x"})
    assert res["ok"] is False and "GEMINI_API_KEY" in res["error"]
    assert (await wa.web_answer({"question": ""}))["error"] == "Savol bo'sh"

    monkeypatch.setattr(cfg, "gemini_api_key", "k")

    class SyncInteractions:  # faqat sync API — to_thread orqali
        def create(self, **body):
            return {"steps": [{"type": "model_output", "content": [{"type": "text", "text": "javob"}]}]}

    monkeypatch.setattr(wa, "_client_factory", lambda key: SimpleNamespace(interactions=SyncInteractions()))
    assert (await wa.web_answer({"question": "x"}))["output"] == "javob"

    class Boom:
        async def create(self, **body):
            raise RuntimeError("403 PERMISSION_DENIED: API key not valid")

    monkeypatch.setattr(wa, "_client_factory", lambda key: SimpleNamespace(aio=SimpleNamespace(interactions=Boom())))
    res = await wa.web_answer({"question": "x"})
    assert res["ok"] is False and "kaliti" in res["error"]

    class Empty:
        async def create(self, **body):
            return SimpleNamespace(steps=[SimpleNamespace(type="model_output", content=[])], output_text=None)

    monkeypatch.setattr(wa, "_client_factory", lambda key: SimpleNamespace(aio=SimpleNamespace(interactions=Empty())))
    assert (await wa.web_answer({"question": "x"}))["error"] == "Model javob qaytarmadi"


def test_web_answer_registered_in_registry():
    from nexus.tools.registry import EXTENSION_MODULES
    from nexus.web_answer import HANDLERS, TOOL_DECLARATIONS

    assert "nexus.web_answer" in EXTENSION_MODULES
    assert TOOL_DECLARATIONS[0]["name"] == "web_answer" and "web_answer" in HANDLERS
    assert TOOL_DECLARATIONS[0]["parameters"]["required"] == ["question"]


# ---------------------------------------------------------------------------
# kill_all (⌥⎋): klient buyruqni ro'yxatdan o'tkazmaydi — registry gate'ni bekor qiladi,
# klient ilgak orqali o'z tool tasklarini bekor qiladi va player'ni tozalaydi
# ---------------------------------------------------------------------------
async def test_client_kill_all_via_registry_hook(monkeypatch):
    from nexus.tools import registry as reg_mod
    from nexus.tools.registry import ToolRegistry

    monkeypatch.setattr(reg_mod, "EXTENSION_MODULES", [])
    bus = EventBus()
    bus.bind_loop()
    registry = ToolRegistry(bus)
    registry.gate.ttl_s = 0.5
    audio = FakeAudio()
    client = GeminiLiveClient(bus, make_settings(), registry, audio)

    # Klient `kill_all` ni ustidan yozmagan — bus handleri registry'niki
    assert bus._handlers["kill_all"] == registry._cmd_kill_all
    assert registry.on_kill_all == client._on_kill_all

    gate_calls: list[str] = []
    real_cancel = registry.gate.cancel_pending
    monkeypatch.setattr(registry.gate, "cancel_pending", lambda src="cancelled": (gate_calls.append(src), real_cancel(src))[1])

    async def fake(a: dict):
        return True, "ok"

    registry._handlers["empty_trash"] = fake
    # Gemini tool_call → klient taski → registry.execute → tasdiq kutilmoqda
    session = FakeSession()
    tc = SimpleNamespace(function_calls=[SimpleNamespace(id="c1", name="empty_trash", args={})])
    await client._handle_message(session, SimpleNamespace(tool_call=tc))
    await asyncio.sleep(0.03)
    assert len(client._tool_tasks) == 1 and bus.state == "awaiting_confirmation"
    audio.player.enqueue(b"\x00" * 64)
    assert audio.player.pending_bytes() == 64

    out = await bus.dispatch_command({"cmd": "kill_all"})
    assert out["ok"] and out["cancelled"] == 1
    assert gate_calls == ["cancelled"]  # ⌥⎋ kutilayotgan tasdiqni bekor qildi
    await asyncio.sleep(0.02)
    assert not client._tool_tasks and registry.gate.pending is None
    assert audio.player.pending_bytes() == 0  # ilgak player'ni tozaladi
    assert bus.state in ("idle", "listening")


async def test_client_kill_all_fallback_without_registry():
    """Registry yo'q (toolsiz rejim) — klient zaxira `kill_all` handlerini ro'yxatdan o'tkazadi."""
    bus = EventBus()
    bus.bind_loop()
    client = GeminiLiveClient(bus, make_settings(), None, FakeAudio())
    assert bus._handlers["kill_all"] == client._cmd_kill_all
    out = await bus.dispatch_command({"cmd": "kill_all"})
    assert out["ok"] and out["cancelled"] == 0


async def test_quota_error_drops_google_search_first(monkeypatch):
    """1011 'exceeded your current quota' → avval google_search grounding olib tashlanadi."""
    from google.genai import types

    client, _bus, _reg, _audio = make_client()
    client.settings.google_search_grounding = True
    client.settings.thinking_level = "medium"
    client.settings.reconnect_base_delay = 0.01
    client.settings.reconnect_max_delay = 0.02

    class Rejecting(FakeLiveConnect):
        def connect(self, *, model, config):
            if len(self.configs) < 1:
                self.configs.append(config)

                class _Bad:
                    async def __aenter__(self_inner):
                        raise RuntimeError("1011 None. You exceeded your current quota, please check your plan")

                    async def __aexit__(self_inner, *exc):
                        return False

                return _Bad()
            return super().connect(model=model, config=config)

    live = Rejecting([FakeSession(turns=[])])
    import google.genai as genai_mod

    monkeypatch.setattr(genai_mod, "Client", lambda api_key: SimpleNamespace(aio=SimpleNamespace(live=live)))
    orig_loop = client._session_loop

    async def _loop(session):
        await orig_loop(session)
        client._stop.set()

    monkeypatch.setattr(client, "_session_loop", _loop)
    await asyncio.wait_for(client.run(), 5)

    assert len(live.configs) == 2
    c1, c2 = live.configs
    assert any(isinstance(t.google_search, types.GoogleSearch) for t in c1.tools)
    assert all(t.google_search is None for t in c2.tools)
    assert c2.thinking_config is not None  # faqat google_search tashlandi, thinking saqlandi


# ---------------------------------------------------------------------------
# BargeInGate — echo cho'qqisi javobni uzmasin
# ---------------------------------------------------------------------------
def test_barge_gate_single_spike_becomes_silence():
    g = am.BargeInGate(chunk_ms=20, min_ms=60, hold_ms=100)  # need = 3
    assert g.process(b"\x01\x01", True, True, 0.0) == ([], 0)  # ushlab turildi
    out, n = g.process(b"\x02\x02", False, True, 0.02)  # jim — cho'qqi echo edi
    assert out == [b"\x00\x00", b"\x00\x00"] and n == 2


def test_barge_gate_sustained_opens_and_holds():
    g = am.BargeInGate(chunk_ms=20, min_ms=60, hold_ms=100)
    g.process(b"a", True, True, 0.00)
    g.process(b"b", True, True, 0.02)
    assert g.process(b"c", True, True, 0.04) == ([b"a", b"b", b"c"], 0)
    assert g.process(b"d", False, True, 0.10) == ([b"d"], 0)  # hold — so'zlar orasidagi pauza
    assert g.process(b"e", False, True, 0.20) == ([b"\x00"], 1)  # hold tugadi


def test_barge_gate_flushes_held_when_playback_stops():
    g = am.BargeInGate(chunk_ms=20, min_ms=60, hold_ms=100)
    g.process(b"a", True, True, 0.0)
    assert g.process(b"b", True, False, 0.02) == ([b"a", b"b"], 0)


def test_player_underrun_grows_prebuffer_and_resets_after_turn():
    p = AudioPlayer(sample_rate=1000, enabled=False, prebuffer_ms=100)  # 200 bayt
    out = bytearray(100)
    p.enqueue(b"\x01\x02" * 100)  # 200 bayt — armed
    p._callback(out, 50, None, None)
    p._callback(out, 50, None, None)
    assert p.armed is True  # navbat yakuniy emas, bufer aynan tugadi — hali underrun emas
    p._callback(out, 50, None, None)  # hech narsa yo'q — underrun
    assert p.underruns == 1 and p.armed is False
    p.enqueue(b"\x01\x02" * 100)  # 200 bayt — endi yetarli emas (300 kerak)
    assert p.armed is False
    p.enqueue(b"\x01\x02" * 50)
    assert p.armed is True
    p.play_out()
    for _ in range(3):
        p._callback(out, 50, None, None)
    assert p.armed is False and p.underruns == 1  # yakuniy navbat tugashi underrun emas
    p.enqueue(b"\x01\x02" * 100)  # yangi javob — yana 200 bayt yetarli
    assert p.armed is True


def test_parse_latency():
    assert am.parse_latency("HIGH") == "high"
    assert am.parse_latency("0.08") == 0.08
    assert am.parse_latency("x") == "high"


def test_wake_defaults_to_name_only(monkeypatch) -> None:
    from nexus.config import Settings
    from nexus.wake import WakeState

    monkeypatch.delenv("WAKE_MODE", raising=False)
    monkeypatch.delenv("WAKE_FOLLOW_UP_S", raising=False)
    s = Settings()
    assert s.wake_mode == "name" and s.wake_follow_up_s == 8.0
    assert WakeState(name="Nexus").mode == "name"


# ---------------------------------------------------------------------------
# Suhbat rejimi ("kel gaplashamiz")
# ---------------------------------------------------------------------------
def test_conversation_phrases() -> None:
    from nexus.wake import ends_conversation, wants_conversation

    for t in ("Kel gaplashamiz", "keling, suhbatlashaylik!", "Давай поговорим", "Let's talk", "gaplashib o'tiraylik"):
        assert wants_conversation(t), t
    for t in ("ertaga gaplashamiz", "Safarini och", "gaplashdingmi u bilan"):
        assert not wants_conversation(t), t
    for t in ("Bo'ldi, rahmat", "suhbatni tugat", "xayr", "ok bye"):
        assert ends_conversation(t), t
    assert ends_conversation("Хватит, пока")
    assert not ends_conversation("rahmat, davom et")


def test_wake_conversation_window_and_expiry(monkeypatch) -> None:
    import nexus.wake as wake_mod
    from nexus.wake import WakeState

    now = [1000.0]
    monkeypatch.setattr(wake_mod.time, "monotonic", lambda: now[0])
    w = WakeState(name="Nexus", mode="name", follow_up_s=8, conversation_idle_s=45)
    assert not w.should_act("qalaysan")
    w.start_conversation()
    now[0] += 30
    assert w.should_act("qalaysan")  # ismsiz — suhbatda
    now[0] += 40  # oxirgi gapdan 40 s (gap oynani yangiladi)
    assert w.should_act("yana bir savol") and not w.conversation_expired
    now[0] += 46
    assert w.conversation_expired and not w.should_act("salom")
    w.stop_conversation()
    assert not w.conversation and not w.engaged
    w.start_conversation()
    w.stop_conversation(follow_up=True)  # "bo'ldi, rahmat" — xayrlashuv javobi eshitilsin
    assert not w.conversation and w.engaged
    now[0] += 9
    assert not w.engaged


async def test_conversation_mode_flow():
    bus = EventBus()
    bus.bind_loop()
    audio = FakeAudio()
    client = GeminiLiveClient(bus, make_settings(wake_mode="name"), FakeRegistry(), audio)
    assert bus.snapshot["SETTINGS"]["conversation"] is False

    # Ismsiz "kel gaplashamiz" → suhbat rejimi yoqiladi va javob beriladi
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="Kel gaplashamiz", finished=True)))
    assert client._addressed is True and client.wake.conversation
    assert bus.snapshot["SETTINGS"]["conversation"] is True
    client._handle_server_content(_sc(turn_complete=True))

    # Keyingi gap ismsiz ham yordamchiga qaratilgan
    client._handle_server_content(
        _sc(input_transcription=SimpleNamespace(text="Koinotda nechta galaktika bor?", finished=True))
    )
    assert client._addressed is True
    client._handle_server_content(_sc(model_turn=SimpleNamespace(parts=[_audio_part()])))
    assert audio.player.pending_bytes() > 0
    client._handle_server_content(_sc(turn_complete=True))

    # "Bo'ldi, rahmat" — shu gapga javob beriladi, keyin rejim tugaydi
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="Bo'ldi, rahmat", finished=True)))
    assert client._addressed is True and not client.wake.conversation
    assert bus.snapshot["SETTINGS"]["conversation"] is False
    client._handle_server_content(_sc(turn_complete=True))
    assert client._addressed is True  # xayrlashuv (tool javobidan keyingi navbat) hali eshitiladi
    client.wake._called_at -= client.wake.follow_up_s + 1
    client._handle_server_content(_sc(input_transcription=SimpleNamespace(text="Safarini och", finished=True)))
    assert client._addressed is False  # yana faqat ism bilan


async def test_conversation_command_and_idle_tick():
    bus = EventBus()
    bus.bind_loop()
    client = GeminiLiveClient(bus, make_settings(wake_mode="name"), FakeRegistry(), FakeAudio())
    r = await bus.dispatch_command({"cmd": "conversation", "value": True})
    assert r["ok"] and r["conversation"] is True
    client.wake._called_at -= client.wake.conversation_idle_s + 1  # 45 s jimlik
    client.tick()
    assert client.wake.conversation is False
    assert bus.snapshot["SETTINGS"]["conversation"] is False


def test_conversation_tools_registered():
    from nexus.tools.registry import ToolRegistry

    r = ToolRegistry()
    assert r.has("start_conversation") and r.has("stop_conversation")
