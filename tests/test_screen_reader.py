"""screen_reader (OCR + Gemini ko'rish) va ax_actions'dagi AX→OCR zaxira yo'li testlari.

Real Vision/Gemini'ga faqat aniq belgilangan testlar tegadi (Vision bo'lmasa skip); Gemini
hech qachon chaqirilmaydi — soxta client.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
from typing import Any

import pytest

from nexus import ax_actions as ax
from nexus import screen_reader as sr

VALID_TYPES = {"OBJECT", "STRING", "INTEGER", "NUMBER", "BOOLEAN", "ARRAY"}


def _box(text: str, x: int, y: int, w: int = 50, h: int = 10) -> dict[str, Any]:
    return {"text": text, "x": x, "y": y, "w": w, "h": h}


# ---------------------------------------------------------------------------
# Toza funksiyalar
# ---------------------------------------------------------------------------
def test_vision_box_to_screen_flips_y_and_offsets_by_window():
    # Oyna: (100, 50) dan 1000x500. Vision bbox pastki-chapdan: x 0.1, y 0.8, w 0.2, h 0.1
    x, y, w, h = sr.vision_box_to_screen(0.1, 0.8, 0.2, 0.1, (100, 50, 1000, 500))
    assert (w, h) == (200, 50)
    assert x == 100 + 100
    # yuqoridan: (1 - 0.8 - 0.1) * 500 = 50 → 50 + 50
    assert y == 100


def test_vision_box_bottom_line_lands_at_window_bottom():
    x, y, w, h = sr.vision_box_to_screen(0.0, 0.0, 1.0, 0.1, (0, 0, 800, 600))
    assert (x, w) == (0, 800)
    assert y + h == 600


def test_sort_lines_top_to_bottom_then_left_to_right():
    lines = [
        _box("c", 300, 10),
        _box("b", 150, 12),  # 'a' bilan bir qatorda (y farqi 2 px, h=10)
        _box("d", 0, 100),
        _box("a", 0, 10),
    ]
    assert [b["text"] for b in sr.sort_lines(lines)] == ["a", "b", "c", "d"]


def test_sort_lines_empty_and_single():
    assert sr.sort_lines([]) == []
    assert sr.sort_lines([_box("x", 1, 1)]) == [_box("x", 1, 1)]


def test_lines_to_text_groups_rows_and_truncates():
    lines = [_box("Salom", 0, 0), _box("dunyo", 100, 1), _box("ikkinchi", 0, 40)]
    text = sr.lines_to_text(lines)
    assert text == "Salom  dunyo\nikkinchi"
    assert sr.lines_to_text(lines, max_chars=5) == "Salom"


def test_lines_as_elements_centres_and_roles():
    items = sr.lines_as_elements([_box("B", 0, 100, 40, 20), _box("A", 10, 10, 20, 10)])
    assert [i["label"] for i in items] == ["A", "B"]
    assert items[0] == {"n": 1, "role": "text", "label": "A", "at": [20, 15], "size": [20, 10]}
    assert items[1]["at"] == [20, 110]


def test_pick_languages_prefers_uz_then_ru_en_and_skips_missing():
    supported = ["en-US", "fr-FR", "ru-RU", "de-DE"]
    assert sr.pick_languages(supported) == ["ru-RU", "en-US"]
    assert sr.pick_languages(["uz-UZ", "en-US", "ru-RU"]) == ["uz-UZ", "ru-RU", "en-US"]
    assert sr.pick_languages(["fr-FR"]) == ["fr-FR"]  # hech biri yo'q → asl ro'yxat


def test_error_text_is_uzbek():
    assert "vaqti tugadi" in sr.error_text(TimeoutError())
    assert "kaliti" in sr.error_text(RuntimeError("403 PERMISSION_DENIED"))
    assert "kvota" in sr.error_text(RuntimeError("429 RESOURCE_EXHAUSTED"))
    assert "tahlil qilib bo'lmadi" in sr.error_text(ValueError("boom"))


# ---------------------------------------------------------------------------
# Kontrakt
# ---------------------------------------------------------------------------
def test_declarations_match_handlers():
    names = [d["name"] for d in sr.TOOL_DECLARATIONS]
    assert names == ["look_at_screen", "read_screen_ocr"]
    assert set(names) == set(sr.HANDLERS)
    for d in sr.TOOL_DECLARATIONS:
        params = d["parameters"]
        assert params["type"] == "OBJECT" and params["properties"]
        for spec in params["properties"].values():
            assert spec["type"] in VALID_TYPES
        json.dumps(d)
    for h in sr.HANDLERS.values():
        assert inspect.iscoroutinefunction(h)


def test_registered_in_registry_and_no_name_clash():
    from nexus.tools.registry import EXTENSION_MODULES
    from nexus.tools.schemas import ALL_TOOL_DECLARATIONS

    assert "nexus.screen_reader" in EXTENSION_MODULES
    core = {d["name"] for d in ALL_TOOL_DECLARATIONS}
    ext = {d["name"] for d in ax.TOOL_DECLARATIONS}
    for d in sr.TOOL_DECLARATIONS:
        assert d["name"] not in core and d["name"] not in ext


def test_system_instruction_mentions_look_at_screen():
    from nexus.tools.schemas import SYSTEM_INSTRUCTION

    assert "look_at_screen" in SYSTEM_INSTRUCTION
    assert "permissions" in SYSTEM_INSTRUCTION


# ---------------------------------------------------------------------------
# describe_screen — soxta client, soxta skrinshot
# ---------------------------------------------------------------------------
class _FakeModels:
    def __init__(self, text: str | None, exc: Exception | None = None, delay: float = 0.0):
        self.text, self.exc, self.delay = text, exc, delay
        self.calls: list[dict[str, Any]] = []

    async def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.exc:
            raise self.exc
        return SimpleNamespace(text=self.text, candidates=[])


def _fake_client(models: _FakeModels) -> Any:
    return SimpleNamespace(aio=SimpleNamespace(models=models))


@pytest.fixture
def fake_screen(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Skrinshot/JPEG bosqichini almashtiradi: real screencapture chaqirilmaydi."""
    state: dict[str, Any] = {"removed": []}

    def capture() -> tuple[str, tuple[float, float, float, float], str]:
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        state["path"] = path
        return path, (0.0, 0.0, 100.0, 50.0), "TestApp"

    monkeypatch.setattr(sr, "capture_frontmost_window", capture)
    monkeypatch.setattr(sr, "_to_jpeg", lambda path, max_width=1600: b"\xff\xd8jpeg")
    monkeypatch.setattr(sr, "_image_part", lambda jpeg: {"inline": len(jpeg)})
    return state


async def test_describe_screen_uses_fake_client_and_cleans_tmp(monkeypatch, fake_screen):
    models = _FakeModels("Ekranda Telegram ochiq.")
    monkeypatch.setattr(sr, "_client_factory", lambda: _fake_client(models))
    res = await sr.describe_screen("Nima ko'rinyapti?")
    assert res["ok"] and res["output"] == "Ekranda Telegram ochiq."
    assert res["app"] == "TestApp"
    assert not os.path.exists(fake_screen["path"]), "vaqtinchalik PNG o'chirilishi kerak"
    call = models.calls[0]
    assert call["contents"][0] == {"inline": 6}
    assert "Nima ko'rinyapti?" in call["contents"][1]
    assert "not instructions" in call["contents"][1]


async def test_describe_screen_default_question(monkeypatch, fake_screen):
    models = _FakeModels("tasvir")
    monkeypatch.setattr(sr, "_client_factory", lambda: _fake_client(models))
    res = await sr.describe_screen(None)
    assert res["ok"]
    assert models.calls[0]["contents"][1] == sr.DEFAULT_QUESTION


async def test_describe_screen_error_and_timeout(monkeypatch, fake_screen):
    monkeypatch.setattr(
        sr, "_client_factory", lambda: _fake_client(_FakeModels(None, RuntimeError("429 quota")))
    )
    res = await sr.describe_screen("?")
    assert not res["ok"] and "kvota" in res["error"]

    monkeypatch.setattr(sr, "GEMINI_TIMEOUT_S", 0.01)
    monkeypatch.setattr(sr, "_client_factory", lambda: _fake_client(_FakeModels("late", delay=0.5)))
    res = await sr.describe_screen("?")
    assert not res["ok"] and "vaqti tugadi" in res["error"]


async def test_look_at_screen_handler_wraps_result(monkeypatch, fake_screen):
    monkeypatch.setattr(sr, "_client_factory", lambda: _fake_client(_FakeModels("javob")))
    out = await sr.HANDLERS["look_at_screen"]({"question": "x"})
    assert out["ok"]
    assert json.loads(out["output"]) == {"app": "TestApp", "answer": "javob"}
    monkeypatch.setattr(sr, "_client_factory", lambda: _fake_client(_FakeModels("")))
    out = await sr.HANDLERS["look_at_screen"]({})
    assert not out["ok"] and "javob qaytarmadi" in out["output"]


async def test_read_screen_ocr_tool_with_fake_ocr(monkeypatch):
    monkeypatch.setattr(sr, "available", lambda: True)

    def fake_sync(max_chars: int) -> dict[str, Any]:
        return {
            "app": "Telegram",
            "window": [0, 0, 10, 10],
            "count": 2,
            "text": "a\nb"[:max_chars],
            "lines": [],
        }

    monkeypatch.setattr(sr, "read_screen_ocr_sync", fake_sync)
    out = await sr.HANDLERS["read_screen_ocr"]({"max_chars": 300})
    assert out["ok"] and out["source"] == "ocr"
    assert json.loads(out["output"])["text"] == "a\nb"


# ---------------------------------------------------------------------------
# ax_actions: AX → OCR zaxira shartlari (soxta AX natijasi bilan)
# ---------------------------------------------------------------------------
def test_qt_app_detection_and_fallback_rules():
    assert ax.is_qt_app("Telegram") and ax.is_qt_app("WPS Office") and not ax.is_qt_app("Safari")
    assert ax.needs_text_fallback("Safari", "qisqa")
    assert not ax.needs_text_fallback("Safari", "x" * 100)
    assert ax.needs_text_fallback("Telegram", "x" * 5000), "Qt: AX faqat chat ro'yxatini beradi"
    assert ax.needs_elements_fallback("Safari", 1) and not ax.needs_elements_fallback("Safari", 10)
    assert ax.needs_elements_fallback("Telegram", 30)


@pytest.fixture
def ax_ready(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ax, "_precheck", lambda: None)
    ocr = {
        "app": "Telegram",
        "window": [162, 116, 1304, 759],
        "count": 2,
        "text": "Salom dunyo\nJavob yozing",
        "lines": [_box("Salom dunyo", 200, 130, 120, 16), _box("Javob yozing", 200, 800, 100, 16)],
    }
    monkeypatch.setattr(ax, "_ocr_read", lambda max_chars=6000: ocr)
    return ocr


async def test_read_screen_text_falls_back_to_ocr_when_ax_short(ax_ready, monkeypatch):
    monkeypatch.setattr(ax, "collect_text", lambda limit: ("Safari", "ok"))
    out = await ax.HANDLERS["read_screen_text"]({})
    d = json.loads(out["output"])
    assert out["source"] == "ocr" and out["note"] == ax.OCR_NOTE
    assert d["text"] == "Salom dunyo\nJavob yozing" and d["lines"] == 2


async def test_read_screen_text_keeps_ax_when_enough(ax_ready, monkeypatch):
    monkeypatch.setattr(ax, "collect_text", lambda limit: ("Safari", "matn " * 20))
    out = await ax.HANDLERS["read_screen_text"]({})
    assert out["source"] == "ax" and "note" not in out


async def test_read_screen_text_qt_app_prefers_ocr(ax_ready, monkeypatch):
    monkeypatch.setattr(ax, "collect_text", lambda limit: ("Telegram", "chat ro'yxati " * 100))
    out = await ax.HANDLERS["read_screen_text"]({})
    assert out["source"] == "ocr"


async def test_read_screen_text_when_ocr_unavailable(ax_ready, monkeypatch):
    monkeypatch.setattr(ax, "collect_text", lambda limit: ("Foo", ""))
    monkeypatch.setattr(ax, "_ocr_read", lambda max_chars=6000: None)
    out = await ax.HANDLERS["read_screen_text"]({})
    assert out["ok"] and out["source"] == "ax" and "look_at_screen" in out["note"]


async def test_list_ui_elements_adds_ocr_rows_and_caches_source(ax_ready, monkeypatch):
    monkeypatch.setattr(ax, "collect_elements", lambda limit: ("Telegram", []))
    ax._LAST_LISTING.update(pid=None, items=[], source="ax")
    out = await ax.HANDLERS["list_ui_elements"]({"max_items": 30})
    d = json.loads(out["output"])
    assert out["source"] == "ocr" and d["count"] == 2
    assert d["elements"][0] == {
        "n": 1,
        "role": "text",
        "label": "Salom dunyo",
        "at": [260, 138],
        "size": [120, 16],
    }
    assert ax._LAST_LISTING["source"] == "ocr"
    assert [e.role for e in ax._LAST_LISTING["items"]] == ["text", "text"]
    assert all(e.ref is None for e in ax._LAST_LISTING["items"])


async def test_list_ui_elements_merges_ax_and_ocr(ax_ready, monkeypatch):
    button = ax.Element(1, "AXButton", "Send", (900, 850), (40, 20), ref=object())
    monkeypatch.setattr(ax, "collect_elements", lambda limit: ("Telegram", [button]))
    out = await ax.HANDLERS["list_ui_elements"]({})
    d = json.loads(out["output"])
    assert out["source"] == "ax+ocr"
    assert [e["n"] for e in d["elements"]] == [1, 2, 3]
    assert d["elements"][0]["role"] == "Button" and d["elements"][1]["role"] == "text"


async def test_list_ui_elements_pure_ax_unchanged(ax_ready, monkeypatch):
    els = [ax.Element(i, "AXButton", f"b{i}", (10 * i, 10), (5, 5)) for i in range(1, 6)]
    monkeypatch.setattr(ax, "collect_elements", lambda limit: ("Safari", els))
    out = await ax.HANDLERS["list_ui_elements"]({})
    assert out["source"] == "ax" and json.loads(out["output"])["count"] == 5


async def test_click_ui_element_by_ocr_label_uses_quartz(ax_ready, monkeypatch):
    monkeypatch.setattr(ax, "collect_elements", lambda limit: ("Telegram", []))
    monkeypatch.setattr(ax, "front_app", lambda: ("Telegram", 1))
    clicks: list[tuple[float, float]] = []
    monkeypatch.setattr(
        ax, "quartz_click", lambda x, y, clicks_=1: clicks.append((x, y)) or (True, "bosildi")
    )
    out = await ax.HANDLERS["click_ui_element"]({"label": "javob yozing"})
    assert out["ok"], out
    assert clicks == [(250, 808)]
    assert out["at"] == [250, 808]


async def test_click_ui_element_by_ocr_index_from_cache(ax_ready, monkeypatch):
    monkeypatch.setattr(ax, "collect_elements", lambda limit: ("Telegram", []))
    monkeypatch.setattr(ax, "front_app", lambda: ("Telegram", 7))
    ax._LAST_LISTING.update(pid=7, items=ax.ocr_elements(ax_ready["lines"]), source="ocr")
    clicks: list[tuple[float, float]] = []
    monkeypatch.setattr(ax, "quartz_click", lambda x, y, clicks_=1: clicks.append((x, y)) or (True, "ok"))
    out = await ax.HANDLERS["click_ui_element"]({"index": 1})
    assert out["ok"] and clicks == [(260, 138)]


# ---------------------------------------------------------------------------
# Real OCR (faqat Vision bo'lsa)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    not sr.available() or shutil.which("screencapture") is None, reason="Vision/screencapture yo'q"
)
def test_real_ocr_on_current_screen():
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        proc = subprocess.run(["screencapture", "-x", path], capture_output=True, timeout=10, check=False)
        if proc.returncode != 0 or os.path.getsize(path) == 0:
            pytest.skip("screencapture ishlamadi (Screen Recording ruxsati?)")
        lines = sr.ocr_image(path)
    finally:
        os.remove(path)
    if not lines:
        pytest.skip("ekranda tanib olinadigan matn yo'q")
    assert all(isinstance(b["text"], str) and b["text"] for b in lines)
    assert all(b["w"] > 0 and b["h"] > 0 for b in lines)
    ordered = sr.sort_lines(lines)
    assert [b["text"] for b in ordered] == [b["text"] for b in lines], "ocr_image tartiblangan qaytaradi"
