"""video_translate: toza funksiyalar, sinxron soat, tool ro'yxatga olinishi, echo guard ilgagi."""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from nexus import video_translate as vt


@pytest.mark.parametrize(
    ("url", "vid"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/watch?list=PL1&v=dQw4w9WgXcQ&t=30", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ?si=abc", "dQw4w9WgXcQ"),
        ("youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://vimeo.com/123", None),
        ("", None),
    ],
)
def test_youtube_id(url: str, vid: str | None) -> None:
    assert vt.youtube_id(url) == vid


def test_build_ffmpeg_cmd() -> None:
    cmd = vt.build_ffmpeg_cmd("ffmpeg", "https://x/a", 12.345)
    assert cmd[cmd.index("-ss") + 1] == "12.35"
    assert "-reconnect" in cmd and cmd[-1] == "pipe:1"
    assert cmd[cmd.index("-ar") + 1] == "16000"
    assert "-ss" not in vt.build_ffmpeg_cmd("ffmpeg", "/tmp/a.m4a", 0.0)


def test_parse_player_state() -> None:
    assert vt.parse_player_state("novideo") is None
    assert vt.parse_player_state("garbage") is None
    assert vt.parse_player_state('{"t": 1.5, "p": false}') == {"t": 1.5, "p": False}


def test_clock_interpolates_and_halts() -> None:
    c = vt.PlaybackClock()
    assert c.halted
    c.update({"t": 10.0, "p": False, "r": 2.0, "d": 100}, now=50.0)
    assert c.position(51.0) == pytest.approx(12.0)
    c.update({"t": 10.0, "p": True}, now=52.0)
    assert c.position(60.0) == pytest.approx(10.0)
    c.update({"t": 10.0, "p": False, "ad": True}, now=60.0)
    assert c.halted


def test_feed_action() -> None:
    la = vt.LOOKAHEAD_S
    assert vt.feed_action(10.0, 10.0, can_resync=True) == "send"
    assert vt.feed_action(10.0 + la - 0.1, 10.0, can_resync=True) == "send"  # oldinda — lookahead ichida
    assert vt.feed_action(10.0 + la + 0.5, 10.0, can_resync=True) == "wait"  # yetarlicha oldinda
    assert vt.feed_action(10.0, 60.0, can_resync=True) == "resync"  # oldinga seek
    assert vt.feed_action(60.0, 10.0, can_resync=True) == "resync"  # orqaga seek
    assert vt.feed_action(10.0, 60.0, can_resync=False) == "send"  # grace: quvib yetadi


def test_fit_tempo() -> None:
    assert vt.fit_tempo(3.0, 3.0) == 1.0
    assert vt.fit_tempo(3.1, 3.0) == 1.0  # <5% farq — tezlashtirilmaydi
    assert vt.fit_tempo(3.6, 3.0) == 1.2
    assert vt.fit_tempo(9.0, 3.0) == vt.MAX_TEMPO
    assert vt.fit_tempo(2.0, 0.0) == vt.MAX_TEMPO
    assert vt.fit_tempo(0.0, 3.0) == 1.0


async def test_time_stretch_shortens_audio() -> None:
    ffmpeg = vt.find_binary("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg yo'q")
    import math
    import struct

    pcm = b"".join(struct.pack("<h", int(8000 * math.sin(i / 10))) for i in range(24000))  # 1 s
    out = await vt.time_stretch(ffmpeg, pcm, 24000, 1.25)
    assert abs(len(out) / 48000 - 0.8) < 0.05
    assert await vt.time_stretch(ffmpeg, pcm, 24000, 1.0) is pcm


def test_translator_instruction_mentions_uzbek() -> None:
    text = vt.translator_instruction("uz")
    assert "Uzbek" in text and "nothing else" in text and "never skip" in text


def test_build_config_native_and_prompt() -> None:
    t = vt.VideoTranslator(settings=SimpleNamespace(gemini_voice="Aoede"))
    native = t._build_config(native=True)
    assert native.translation_config.target_language_code == "uz"
    assert native.realtime_input_config.activity_handling.name == "NO_INTERRUPTION"
    assert t._build_config(native=False).translation_config is None


async def test_start_rejects_non_youtube() -> None:
    res = await vt.VideoTranslator().start("https://example.com", "chrome")
    assert res["ok"] is False and "YouTube" in res["error"]


async def test_stop_without_task() -> None:
    res = await vt.stop_video_translation({})
    assert res["ok"] and "yo'q" in res["output"]


def test_tools_registered_in_registry() -> None:
    from nexus.tools.registry import ToolRegistry

    r = ToolRegistry()
    assert r.has("translate_video") and r.has("stop_video_translation")


def test_attach_sets_echo_hook() -> None:
    audio = SimpleNamespace(extra_playing=None)
    tr = vt.attach(bus=None, settings=None, audio=audio)
    assert audio.extra_playing == tr.is_playing
    assert audio.extra_playing() is False


def test_player_setup_js() -> None:
    js = vt.player_setup_js(0.0, play=False)
    assert "v.muted=true" in js and "v.pause()" in js
    js = vt.player_setup_js(0.2, play=True)
    assert "v.volume=0.200" in js and "v.play()" in js


def test_build_ytdlp_cmd() -> None:
    cmd = vt.build_ytdlp_cmd("yt-dlp", "https://youtu.be/x", "/tmp/d")
    assert "after_move:filepath" in cmd and "!is_live" in cmd
    assert cmd[cmd.index("-o") + 1].startswith(os.path.join("/tmp/d", ""))


def test_segmenter_cuts_on_quiet_after_min() -> None:
    seg = vt.Segmenter(min_s=1.0, max_s=5.0, quiet_ratio=0.5)
    assert not any(seg.push(0.2) for _ in range(9))  # 0.9 s
    assert not seg.push(0.2)  # 1.0 s, baland
    assert seg.push(0.05)  # jimlik → kesish
    assert seg.length_s == 0.0


def test_segmenter_cuts_at_max() -> None:
    seg = vt.Segmenter(min_s=1.0, max_s=2.0)
    results = [seg.push(0.3) for _ in range(20)]
    assert results.index(True) == 19  # 2.0 s


def test_player_hold_outputs_silence() -> None:
    from nexus.audio_streamer import AudioPlayer

    p = AudioPlayer(enabled=False)
    p.enqueue(b"\x01\x00" * 480)
    p.hold = True
    out = bytearray(960)
    p._callback(out, 480, None, None)
    assert bytes(out) == b"\x00" * 960 and p.pending_bytes() == 960
    p.hold = False
    p._callback(out, 480, None, None)
    assert bytes(out) == b"\x01\x00" * 480 and p.pending_bytes() == 0


def test_video_tab_script_targets_tab_by_id() -> None:
    chrome = vt.video_tab_script("chrome", 'abc"; do evil', "return 1")
    assert 'contains "abcdoevil"' in chrome and "execute t javascript" in chrome
    assert vt.NO_TAB in chrome
    assert 'do JavaScript "return 1" in t' in vt.video_tab_script("safari", "abc", "return 1")


def test_video_tab_script_prefers_chrome_tab_id() -> None:
    script = vt.video_tab_script("chrome", "abc", "1", tab_id="123x")
    assert '(id of t as text) is "123"' in script and "contains" not in script
    assert 'contains "abc"' in vt.video_tab_script("safari", "abc", "1", tab_id="123")


def test_player_setup_js_keeps_volume_when_negative() -> None:
    js = vt.player_setup_js(-1, play=False)
    assert "muted" not in js and "volume" not in js and "v.pause()" in js


def test_ready_needs_translation_ahead() -> None:
    t = vt.VideoTranslator()
    assert not t._ready(10.0)
    t._ready_until = 10.0 + vt.GATE_AHEAD_S
    assert t._ready(10.0)
    t._ready_until, t._eof = 0.0, True  # audio tugadi, navbat bo'sh
    assert t._ready(10.0)


@pytest.mark.parametrize(
    ("text", "junk"),
    [
        ("(Uzbek translation: Xullas, bilasizmi)", True),
        ("<no speech>{pause}", True),
        ('{"pause": true}', True),
        ("Ammo keyin eng qiziq voqea sodir bo'ldi.", False),
        ("72 soat ichida 90 bet yozdim.", False),
        ("(Uzbek): ikki kecha uxlamay", True),
        ("O'zbekcha: salom", True),
        ("O'zbekistonda yashayman.", False),
    ],
)
def test_is_junk_translation(text: str, junk: bool) -> None:
    assert vt.is_junk_translation(text) is junk


def test_is_quota_error() -> None:
    assert vt.is_quota_error(RuntimeError("1011 None. You exceeded your current quota, please check"))
    assert vt.is_quota_error(RuntimeError("RESOURCE_EXHAUSTED"))
    assert not vt.is_quota_error(RuntimeError("1006 abnormal closure"))


class _FakePlayer:
    sample_rate = 24000
    hold = False

    def __init__(self) -> None:
        self.chunks: list[bytes] = []

    def enqueue(self, data: bytes) -> None:
        self.chunks.append(data)

    def pending_bytes(self) -> int:
        return 0

    def play_out(self) -> None:
        pass


def test_pump_assigns_only_closed_segments_in_order() -> None:
    t = vt.VideoTranslator()
    w = vt._Worker(0)
    w.connected = True
    t._free.append(w)
    open_seg = vt.Segment(seq=0, buf=[b"a"])
    t._unassigned.append(open_seg)
    t._pump()
    assert w.inbox.empty() and w.seg is None  # hali yig'ilyapti
    t._close(open_seg)
    items = [w.inbox.get_nowait() for _ in range(w.inbox.qsize())]
    assert items == [("start", open_seg), b"a", ("end", open_seg)]
    assert w.seg is open_seg and not t._free


async def test_playout_plays_in_order_at_video_time() -> None:
    import asyncio
    import time

    t = vt.VideoTranslator()
    t.player = _FakePlayer()
    t.clock.update({"t": 10.0, "p": False}, time.monotonic())
    second = vt.Segment(seq=1, src_start=13.0, src_end=16.0, done=True, audio_bytes=4)
    second.audio.append(b"BBBB")
    first = vt.Segment(seq=0, src_start=10.0, src_end=13.0, done=True, audio_bytes=4, text="salom")
    first.audio.append(b"AAAA")
    t._segments = {1: second, 0: first}
    task = asyncio.create_task(t._playout())
    await asyncio.sleep(0.2)
    assert t.player.chunks == [b"AAAA"]  # ikkinchisi video 13 s ga yetguncha kutadi
    t.clock.update({"t": 13.0, "p": False}, time.monotonic())
    await asyncio.sleep(0.2)
    task.cancel()
    assert t.player.chunks == [b"AAAA", b"BBBB"]
    assert [s.seq for s in t.history] == [0, 1] and t._ready_until == 16.0


async def test_playout_streams_segment_still_arriving() -> None:
    import asyncio
    import time

    t = vt.VideoTranslator()
    t.player = _FakePlayer()
    t.clock.update({"t": 0.0, "p": False}, time.monotonic())
    seg = vt.Segment(seq=0, src_start=0.0, src_end=3.0, audio_bytes=2, first_audio_at=time.monotonic())
    seg.audio.append(b"x1")
    t._segments = {0: seg}
    task = asyncio.create_task(t._playout())
    await asyncio.sleep(0.1)
    seg.audio.append(b"x2")
    seg.done = True
    await asyncio.sleep(0.1)
    task.cancel()
    assert t.player.chunks == [b"x1", b"x2"] and seg.tempo == 1.0 and t.history == [seg]


async def test_playout_drops_junk_translation() -> None:
    import asyncio
    import time

    t = vt.VideoTranslator()
    t.player = _FakePlayer()
    t.clock.update({"t": 0.0, "p": False}, time.monotonic())
    seg = vt.Segment(seq=0, src_start=0.0, src_end=3.0, done=True, audio_bytes=2, text="<no speech>")
    seg.audio.append(b"zz")
    t._segments = {0: seg}
    task = asyncio.create_task(t._playout())
    await asyncio.sleep(0.1)
    task.cancel()
    assert t.player.chunks == [] and t.junk == 1


def test_silent_segment_is_not_sent() -> None:
    t = vt.VideoTranslator()
    w = vt._Worker(0)
    w.connected = True
    t._free.append(w)
    quiet = vt.Segment(seq=0, input=[b"q"] * 10, buf=[b"q"] * 10, rms_sum=0.001 * 10)
    t._unassigned.append(quiet)
    t._close(quiet)
    assert quiet.done and w.inbox.empty() and list(t._free) == [w]  # sessiya band qilinmadi
    loud = vt.Segment(seq=1, input=[b"l"] * 10, buf=[b"l"] * 10, rms_sum=0.1 * 10)
    assert not vt.is_silent(loud)


def test_find_tab_script_activates_existing_tab() -> None:
    script = vt.find_tab_script('abc"x')
    assert 'contains "abcx"' in script and "set active tab index of w to i" in script


def test_ready_counts_answered_and_silent_gaps() -> None:
    t = vt.VideoTranslator()
    answered = vt.Segment(seq=0, src_start=400.5, src_end=402.0, done=True, audio_bytes=100)
    waiting = vt.Segment(seq=1, src_start=402.0, src_end=405.0)
    t._segments = {0: answered, 1: waiting}
    assert not t._ready(400.0)  # 402–405 javobi hali yo'q
    waiting.audio_bytes = 48000  # 1 s audio keldi
    assert t._ready(400.0)
    gap = vt.VideoTranslator()  # oldinda bo'lak yo'q (jimlik) — tayyor
    gap._segments = {0: vt.Segment(seq=0, src_start=410.0, src_end=412.0)}
    assert gap._ready(400.0)
    dropped = vt.VideoTranslator()  # seek'da tashlangan bo'lak hisobga olinmaydi
    dropped._segments = {0: vt.Segment(seq=0, src_start=0.0, src_end=3.0, seek_dropped=True, done=True)}
    assert not dropped._ready(0.0) or dropped._eof


def test_on_content_retries_junk_and_closes_session() -> None:
    from types import SimpleNamespace as NS

    t = vt.VideoTranslator()
    w = vt._Worker(0)
    seg = vt.Segment(seq=0, input=[b"a"], worker=w)
    w.seg = seg
    audio = NS(model_turn=NS(parts=[NS(inline_data=NS(data=b"zz"), text=None)]),
               output_transcription=NS(text="<no speech>"), generation_complete=None, turn_complete=None)
    assert t._on_content(w, audio) is False and seg.audio_bytes == 2
    end = NS(model_turn=None, output_transcription=None, generation_complete=True, turn_complete=None)
    assert t._on_content(w, end) is True  # sessiya yopiladi
    assert seg.retries == 1 and not seg.done and seg.audio_bytes == 0 and seg.text == ""
    assert list(t._unassigned) == [seg] and w.seg is None
    good = vt.Segment(seq=1, input=[b"a"], worker=w)
    w.seg = good
    good.text = "Salom"
    assert t._on_content(w, end) is True and good.done
