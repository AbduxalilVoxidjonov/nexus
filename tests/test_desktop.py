"""nexus.desktop — GUI'siz (sof-Python) qismlarning testlari.

Cocoa oynasi/orb/menyu bar ochilmaydi: pozitsiya saqlash, holat→rang/yorliq, argv → DesktopOptions,
server tayyorligini kutish (soxta health probe), placeholder sahifa, main.desktop_mode.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from nexus import desktop
from nexus.desktop import (
    ORB_SIZE,
    STATE_COLORS,
    STATE_LABELS,
    WINDOW_MIN_SIZE,
    DesktopOptions,
    DesktopPrefs,
    default_orb_origin,
    default_window_frame,
    effective_state,
    placeholder_html,
    rect_on_screens,
    state_style,
    status_title,
    wait_for_server,
)
from nexus.main import build_parser, desktop_mode


# ---------------------------------------------------------------------------
# Holat → rang / yorliq
# ---------------------------------------------------------------------------
def test_state_tables_are_complete() -> None:
    assert set(STATE_COLORS) == set(STATE_LABELS)
    for st in ("idle", "listening", "processing", "tool_executing", "speaking", "dictating", "awaiting_confirmation"):
        assert st in STATE_COLORS


@pytest.mark.parametrize(
    ("state", "color"),
    [
        ("idle", "#6b7280"),
        ("listening", "#22c55e"),
        ("processing", "#f59e0b"),
        ("tool_executing", "#34d399"),
        ("speaking", "#06b6d4"),
        ("dictating", "#a855f7"),
        ("awaiting_confirmation", "#f59e0b"),
    ],
)
def test_state_style_colors(state: str, color: str) -> None:
    assert state_style(state)[0] == color


def test_effective_state_priorities() -> None:
    assert effective_state("listening", daemon_alive=False) == "stopped"
    assert effective_state("listening", gemini="disconnected") == "disconnected"
    assert effective_state("listening", gemini="reconnecting") == "connecting"
    assert effective_state("listening", pending_confirm=True) == "awaiting_confirmation"
    assert effective_state("nonexistent_state") == "idle"
    assert effective_state("speaking") == "speaking"


def test_status_title_menu_text() -> None:
    assert status_title("listening") == "● Tinglamoqda"
    assert status_title("idle", muted=True) == "● Kutmoqda (mikrofon o'chiq)"
    assert status_title("idle", gemini="disconnected") == "● Ulanmagan"
    assert state_style("idle", gemini="disconnected")[0] == "#ef4444"


def test_orb_html_colors_match_python() -> None:
    """ui/orb.html ichidagi ranglar jadvali desktop.py bilan bir xil bo'lishi kerak."""
    html = (Path(__file__).resolve().parent.parent / "ui" / "orb.html").read_text(encoding="utf-8")
    for st, color in STATE_COLORS.items():
        if st in ("stopped",):  # orb sahifasi daemon to'xtaganini ko'rmaydi (WS uziladi)
            continue
        assert f'{st}: "{color}"' in html, f"orb.html'da {st} rangi {color} emas"


# ---------------------------------------------------------------------------
# Sozlamalar (pozitsiya saqlash/o'qish)
# ---------------------------------------------------------------------------
def test_prefs_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "sub" / "desktop.json"
    prefs = DesktopPrefs(p)
    assert prefs.orb_position is None
    assert prefs.window_frame is None
    assert prefs.orb_visible is True

    prefs.set_orb_position(1673.04, 9.0)
    prefs.set_window_frame(90, 116, 1343.3, 961)
    prefs.set_orb_visible(False)
    assert prefs.save() is True
    assert p.is_file()
    assert not p.with_suffix(".json.tmp").exists()

    again = DesktopPrefs(p)
    assert again.orb_position == (1673.0, 9.0)
    assert again.window_frame == (90.0, 116.0, 1343.3, 961.0)
    assert again.orb_visible is False


def test_prefs_ignores_corrupt_or_invalid(tmp_path: Path) -> None:
    p = tmp_path / "desktop.json"
    p.write_text("{not json", encoding="utf-8")
    assert DesktopPrefs(p).data == {}

    p.write_text(json.dumps({"orb": {"x": "abc"}, "window": {"x": 0, "y": 0, "w": 10, "h": 10}}), encoding="utf-8")
    prefs = DesktopPrefs(p)
    assert prefs.orb_position is None
    assert prefs.window_frame is None  # juda kichik oyna e'tiborga olinmaydi

    p.write_text("[1, 2]", encoding="utf-8")
    assert DesktopPrefs(p).data == {}


def test_prefs_save_failure_is_soft(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    prefs = DesktopPrefs(blocker / "desktop.json")  # ota "papka" — oddiy fayl → OSError
    prefs.set_orb_position(1, 2)
    assert prefs.save() is False


# ---------------------------------------------------------------------------
# Geometriya
# ---------------------------------------------------------------------------
def test_rect_on_screens() -> None:
    screens = [(0, 0, 1800, 1169), (1800, 0, 1920, 1080)]
    assert rect_on_screens((100, 100, 128, 148), screens)
    assert rect_on_screens((1850, 50, 128, 148), screens)
    assert not rect_on_screens((5000, 5000, 128, 148), screens)
    assert not rect_on_screens((-120, 100, 128, 148), screens)  # faqat 8px ko'rinadi
    assert rect_on_screens((-80, 100, 128, 148), screens)  # 48px ko'rinadi


def test_default_orb_origin_bottom_right() -> None:
    x, y = default_orb_origin((0, 90, 1800, 1054))
    assert x == 1800 - ORB_SIZE[0] - desktop.ORB_MARGIN
    assert y == 90 + desktop.ORB_MARGIN


def test_default_window_frame_is_90_percent_centered() -> None:
    x, y, w, h = default_window_frame((0, 90, 1800, 1054))
    assert w == pytest.approx(1800 * 0.9)
    assert h == pytest.approx(1054 * 0.9)
    assert x == pytest.approx((1800 - w) / 2)
    assert y == pytest.approx(90 + (1054 - h) / 2)


def test_default_window_frame_respects_min_size() -> None:
    _x, _y, w, h = default_window_frame((0, 0, 1000, 700))
    assert (w, h) == WINDOW_MIN_SIZE
    # ekran min o'lchamdan ham kichik bo'lsa — ekranga sig'adi
    _x, _y, w, h = default_window_frame((0, 0, 800, 600))
    assert (w, h) == (800, 600)


# ---------------------------------------------------------------------------
# argv → DesktopOptions, main.desktop_mode
# ---------------------------------------------------------------------------
def test_options_from_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEXUS_HIDE_DOCK", raising=False)
    parser = build_parser()
    o = DesktopOptions.from_args(parser.parse_args([]))
    assert (o.window, o.orb, o.hide_dock) == (True, True, False)
    o = DesktopOptions.from_args(parser.parse_args(["--no-orb", "--no-window"]))
    assert (o.window, o.orb) == (False, False)
    monkeypatch.setenv("NEXUS_HIDE_DOCK", "true")
    assert DesktopOptions.from_args(argparse.Namespace()).hide_dock is True


def test_desktop_mode_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    parser = build_parser()
    monkeypatch.setattr(desktop.sys, "platform", "darwin")
    assert desktop_mode(parser.parse_args([])) is True
    assert desktop_mode(parser.parse_args(["--no-orb"])) is True
    assert desktop_mode(parser.parse_args(["--headless"])) is False
    assert desktop_mode(parser.parse_args(["--no-ui"])) is False
    assert desktop_mode(parser.parse_args(["--text", "salom"])) is False
    monkeypatch.setattr(desktop.sys, "platform", "linux")
    assert desktop_mode(parser.parse_args([])) is False


# ---------------------------------------------------------------------------
# Server tayyorligini kutish (soxta health)
# ---------------------------------------------------------------------------
def test_wait_for_server_succeeds_after_retries() -> None:
    calls: list[str] = []
    slept: list[float] = []

    def probe(url: str) -> bool:
        calls.append(url)
        return len(calls) >= 3

    ok = wait_for_server(
        "http://127.0.0.1:8765/", timeout=10, interval=0.25, probe=probe, sleep=slept.append, clock=lambda: 0.0
    )
    assert ok is True
    assert calls == ["http://127.0.0.1:8765/health"] * 3
    assert slept == [0.25, 0.25]


def test_wait_for_server_times_out() -> None:
    t = {"now": 0.0}

    def sleep(s: float) -> None:
        t["now"] += s

    ok = wait_for_server("http://x", timeout=1.0, interval=0.5, probe=lambda _u: False, sleep=sleep, clock=lambda: t["now"])
    assert ok is False
    assert t["now"] >= 1.0


def test_wait_for_server_stops_when_daemon_dies() -> None:
    alive = iter([True, False])
    slept: list[float] = []
    ok = wait_for_server(
        "http://x",
        timeout=100,
        probe=lambda _u: False,
        keep_waiting=lambda: next(alive),
        sleep=slept.append,
        clock=lambda: 0.0,
    )
    assert ok is False
    assert len(slept) == 1  # ikkinchi tekshiruvda daemon o'lgan — darhol qaytadi


def test_wait_for_server_real_probe_refuses_closed_port() -> None:
    # Hech kim tinglamayotgan port — real _http_ok False qaytaradi, xato tashlamaydi
    ok = wait_for_server("http://127.0.0.1:1", timeout=0.3, interval=0.1)
    assert ok is False


# ---------------------------------------------------------------------------
# Placeholder sahifa
# ---------------------------------------------------------------------------
def test_placeholder_html() -> None:
    html = placeholder_html("Nexus ishga tushmoqda…", "audio · UI")
    assert "<!DOCTYPE html>" in html and 'class="spin"' in html and "Nexus ishga tushmoqda…" in html
    err = placeholder_html("Xato", "detail", spinner=False)
    assert 'class="err"' in err and "detail" in err and "spin" not in err.split("<body>")[1]


def test_load_extra_env_reads_home_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from nexus.main import load_extra_env

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEXUS_TEST_EXTRA", raising=False)
    assert load_extra_env() == []  # fayl yo'q
    envdir = tmp_path / ".nexus"
    envdir.mkdir()
    (envdir / ".env").write_text("NEXUS_TEST_EXTRA=1\n", encoding="utf-8")
    assert load_extra_env() == [envdir / ".env"]
    assert desktop.os.getenv("NEXUS_TEST_EXTRA") == "1"


# ---------------------------------------------------------------------------
# nexus.config: `.env` manbalari modul yuklanishida (`~/.nexus/.env` ham) — Settings() ko'radi
# ---------------------------------------------------------------------------
def test_config_loads_home_env_into_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import importlib

    import nexus.config as cfg

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)  # CWD `.env` yo'q
    monkeypatch.setattr(cfg, "_project_env", lambda: None)  # loyiha `.env` i ham chetlab o'tiladi
    monkeypatch.delenv("WAKE_NAME", raising=False)
    monkeypatch.delenv("NEXUS_TEST_HOME_ENV", raising=False)

    envdir = tmp_path / ".nexus"
    envdir.mkdir()
    (envdir / ".env").write_text("WAKE_NAME=UyNexus\nNEXUS_TEST_HOME_ENV=1\n", encoding="utf-8")

    assert cfg.env_candidates() == [envdir / ".env"]
    assert cfg.load_env_files() == [envdir / ".env"]
    assert cfg.Settings().wake_name == "UyNexus"  # yangi Settings() ham ko'radi
    assert cfg.load_extra_env() == [envdir / ".env"]  # mos kelish: main.load_extra_env → config

    # override=False: mavjud muhit o'zgaruvchisi ustun
    monkeypatch.setenv("WAKE_NAME", "Muhit")
    cfg.load_env_files()
    assert cfg.Settings().wake_name == "Muhit"

    # Modul qayta yuklanganda ham (haqiqiy import vaqti holati) singleton `~/.nexus/.env` ni ko'radi
    monkeypatch.delenv("WAKE_NAME", raising=False)
    monkeypatch.delenv("NEXUS_TEST_HOME_ENV", raising=False)
    old_settings = cfg.settings
    try:
        reloaded = importlib.reload(cfg)
        # reload'da `_project_env` asl holiga qaytadi — loyiha .env WAKE_NAME bermasa bu tekshiruv o'tadi;
        # ishonchli belgi sifatida faqat ~/.nexus/.env da bo'lgan o'zgaruvchini tekshiramiz
        assert desktop.os.getenv("NEXUS_TEST_HOME_ENV") == "1"
        assert reloaded.settings is not old_settings
    finally:
        importlib.reload(cfg)
        cfg.settings = old_settings  # boshqa testlar/modullar uchun avvalgi singleton


def test_config_placeholder_api_key_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    from nexus.config import Settings, is_placeholder_api_key

    for ph in ("your_api_key_here", "SIZNING_API_KEY", '"your_api_key_here"', "  ", "", "Your_Key"):
        assert is_placeholder_api_key(ph), ph
        monkeypatch.setenv("GEMINI_API_KEY", ph)
        assert Settings().gemini_api_key == ""
    assert not is_placeholder_api_key("AIzaSyRealLookingKey123")
    monkeypatch.setenv("GEMINI_API_KEY", "  AIzaSyRealLookingKey123 ")
    assert Settings().gemini_api_key == "AIzaSyRealLookingKey123"


def test_start_command_warns_on_placeholder_key(tmp_path: Path) -> None:
    """start.command: bo'sh/namunaviy GEMINI_API_KEY → Sozlamalarga yo'naltiruvchi ogohlantirish, lekin
    ishga tushish davom etadi (kalit ilovada kiritiladi); haqiqiy kalit → ogohlantirishsiz."""
    import shutil
    import subprocess

    zsh = shutil.which("zsh")
    if zsh is None:
        pytest.skip("zsh yo'q")
    root = Path(__file__).resolve().parent.parent
    script = (root / "start.command").read_text(encoding="utf-8")
    # Faqat .env tekshiruvi qismini ajratib olamiz (venv/pgrep/exec qismlarisiz)
    start = script.index("# GEMINI_API_KEY:")
    end = script.index('echo "Nexus Ovoz OS ishga tushmoqda..."')
    snippet = "pause() { return 0; }\ncd " + str(tmp_path) + "\n" + script[start:end] + "\necho PASSED\n"
    for value, ok in (
        ("your_api_key_here", False),
        ("SIZNING_API_KEY", False),
        ('"your_api_key_here"', False),
        ("", False),
        ("AIzaSyRealLookingKey123", True),
    ):
        (tmp_path / ".env").write_text(f"GEMINI_API_KEY={value}\n", encoding="utf-8")
        proc = subprocess.run([zsh, "-c", snippet], capture_output=True, text=True, timeout=10, check=False)
        assert proc.returncode == 0 and "PASSED" in proc.stdout, (value, proc.stdout, proc.stderr)
        if ok:
            assert "DIQQAT" not in proc.stdout, proc.stdout
        else:
            assert "GEMINI_API_KEY" in proc.stdout and "Sozlamalar" in proc.stdout, (value, proc.stdout)
            assert "aistudio.google.com" in proc.stdout


# ---------------------------------------------------------------------------
# MetricsTicker: snapshot'dagi reconnects/audio_dropped saqlanadi
# ---------------------------------------------------------------------------
async def test_metrics_ticker_preserves_snapshot_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from nexus.events import EventBus
    from nexus.main import MetricsTicker

    bus = EventBus()
    bus.bind_loop()
    bus.publish("METRICS", {"reconnects": 2, "audio_dropped": 7, "latency_ms": 321, "cpu": 99.0})
    q = bus.subscribe()
    ticker = MetricsTicker(bus, interval=0.01, gemini=None)

    async def fake_info() -> dict:
        return {"cpu_percent": 12.0, "ram_percent": 40.0, "battery_percent": 80}

    monkeypatch.setattr(ticker, "_info", fake_info)
    task = asyncio.create_task(ticker.run())
    ev = await asyncio.wait_for(q.get(), 1.0)
    task.cancel()
    assert ev["type"] == "METRICS"
    d = ev["data"]
    assert d["reconnects"] == 2 and d["audio_dropped"] == 7  # eski qiymatlar saqlandi
    assert d["cpu"] == 12.0 and d["ram"] == 40.0 and d["battery"] == 80  # yangi qiymatlar ustun
    assert d["latency_ms"] == 321  # gemini o'lchovi yo'q — snapshot'dagi oxirgisi qoladi
    assert "uptime_s" in d
    # snapshot ham to'liq qoladi
    assert bus.snapshot["METRICS"]["reconnects"] == 2

    # gemini latency bo'lsa u ustun
    ticker.gemini = type("G", (), {"last_latency_ms": 55})()
    assert ticker.build_payload({"cpu": 1.0})["latency_ms"] == 55
