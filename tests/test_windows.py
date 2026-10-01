"""Windows qatlami: macOS'da ham ishlaydigan (OS chaqiruvlari mock qilingan) testlar."""
from __future__ import annotations

import pytest

from nexus import windows_actions as wa
from nexus.tools import registry as reg_mod
from nexus.tools.schemas import ALL_TOOL_DECLARATIONS


def test_supported_tools_exist_in_schemas():
    names = {d["name"] for d in ALL_TOOL_DECLARATIONS}
    assert wa.SUPPORTED_TOOLS <= names


def test_registry_on_windows_filters_declarations(monkeypatch):
    monkeypatch.setattr(reg_mod, "IS_WINDOWS", True)
    reg = reg_mod.ToolRegistry(None, None)
    names = {d["name"] for d in reg.declarations()}
    assert isinstance(reg.mac, wa.WindowsController)
    assert isinstance(reg.tabs, wa.WindowsBrowserController)
    assert wa.SUPPORTED_TOOLS <= names
    assert "set_brightness" not in names and "browser_click_button" not in names
    assert set(reg.extensions) <= wa.SUPPORTED_EXTENSIONS
    assert not any(n.startswith(("read_screen", "ax_")) for n in names)


def test_registry_on_macos_keeps_all(monkeypatch):
    monkeypatch.setattr(reg_mod, "IS_WINDOWS", False)
    reg = reg_mod.ToolRegistry(None, None)
    names = {d["name"] for d in reg.declarations()}
    assert {d["name"] for d in ALL_TOOL_DECLARATIONS} <= names


@pytest.fixture
def keys(monkeypatch):
    pressed: list[tuple[int, int]] = []
    monkeypatch.setattr(wa, "_press_key", lambda vk, times=1: pressed.append((vk, times)))
    return pressed


async def test_volume_step_presses_keys(keys):
    ok, _ = await wa.WindowsController().volume_step(10)
    assert ok and keys == [(wa.VK_VOLUME_UP, 5)]
    keys.clear()
    ok, _ = await wa.WindowsController().volume_step(-3)
    assert ok and keys == [(wa.VK_VOLUME_DOWN, 2)]


async def test_set_volume_goes_to_zero_then_up(keys):
    ok, out = await wa.WindowsController().set_volume(40)
    assert ok and "40%" in out
    assert keys == [(wa.VK_VOLUME_DOWN, 50), (wa.VK_VOLUME_UP, 20)]


async def test_media_control(keys):
    c = wa.WindowsController()
    assert (await c.media_control("next"))[0] and keys[-1] == (wa.VK_MEDIA_NEXT_TRACK, 1)
    ok, out = await c.media_control("rewind")
    assert not ok and "Noma'lum" in out


async def test_launch_app_uses_start_menu(monkeypatch, tmp_path):
    lnk = tmp_path / "Google Chrome.lnk"
    lnk.write_text("")
    monkeypatch.setattr(wa, "start_menu_apps", lambda refresh=False: {"Google Chrome": lnk, "Notepad++": tmp_path})
    opened: list[str] = []
    monkeypatch.setattr(wa.os, "startfile", opened.append, raising=False)
    ok, out = await wa.WindowsController().launch_app("chrome")
    assert ok and opened == [str(lnk)] and "Google Chrome" in out


async def test_quit_app_refuses_protected():
    ok, out = await wa.WindowsController().quit_app("explorer.exe")
    assert not ok and "mumkin emas" in out


async def test_clipboard_passes_text_via_stdin(monkeypatch):
    calls: list[tuple[str, bytes | None]] = []

    async def fake_ps(script, timeout=15.0, stdin=None):
        calls.append((script, stdin))
        return True, ""

    monkeypatch.setattr(wa, "run_powershell", fake_ps)
    ok, _ = await wa.WindowsController().set_clipboard("salom 'dunyo' $env:X")
    assert ok
    script, stdin = calls[0]
    assert stdin == b"salom 'dunyo' $env:X"
    assert "salom" not in script  # matn skriptga qo'shilmaydi — injection yo'q


def test_ps_quote_escapes_single_quotes():
    assert wa._ps_quote("a'b") == "'a''b'"


def test_platform_controller_picks_by_os(monkeypatch):
    from nexus import main

    monkeypatch.setattr(main.sys, "platform", "win32")
    assert isinstance(main.platform_controller(), wa.WindowsController)
    monkeypatch.setattr(main.sys, "platform", "darwin")
    assert type(main.platform_controller()).__name__ == "MacOSController"


def test_walk_find(tmp_path):
    from nexus.file_actions import _walk_find

    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "Hisobot_2026.xlsx").write_text("")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "hisobot.txt").write_text("")
    found = _walk_find(tmp_path, "hisobot", 10)
    assert [p.endswith("Hisobot_2026.xlsx") for p in found] == [True]


def test_windows_sensitive_suffixes():
    from nexus.safety import path_is_sensitive

    assert path_is_sensitive("~/Desktop/run.bat")
    assert path_is_sensitive("~/Desktop/x.ps1")
    assert not path_is_sensitive("~/Desktop/hisobot.txt")
