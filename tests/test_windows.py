"""Windows qatlami: macOS'da ham ishlaydigan (OS chaqiruvlari mock qilingan) testlar."""
from __future__ import annotations

import sys

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


# ---------------------------------------------------------------------------
# 2-bosqich: klaviatura va terminal qo'riqchisi
# ---------------------------------------------------------------------------
from nexus import windows_input as wi


@pytest.mark.parametrize(
    ("keys", "mods", "key"),
    [
        ("ctrl+s", [wi.VK_CONTROL], ord("S")),
        ("cmd+c", [wi.VK_CONTROL], ord("C")),  # macOS yozuvi → Ctrl
        ("cmd+shift+4", [wi.VK_CONTROL, wi.VK_SHIFT], ord("4")),
        ("alt+f4", [wi.VK_MENU], 0x73),
        ("win+d", [wi.VK_LWIN], ord("D")),
        ("enter", [], 0x0D),
        ("Ctrl + Left", [wi.VK_CONTROL], 0x25),
        ("ctrl-z", [wi.VK_CONTROL], ord("Z")),
        ("win", [], wi.VK_LWIN),
    ],
)
def test_parse_hotkey(keys, mods, key):
    assert wi.parse_hotkey(keys) == (mods, key)


@pytest.mark.parametrize("keys", ["", "ctrl", "ctrl+a+b", "ctrl+nokey"])
def test_parse_hotkey_errors(keys):
    with pytest.raises(wi.HotkeyError):
        wi.parse_hotkey(keys)


def test_text_events_unicode_and_newline():
    ev = wi.text_events("oʻ\n😀")
    units = [scan for vk, scan, fl in ev if fl == wi.KEYEVENTF_UNICODE]
    assert units[:2] == [ord("o"), ord("ʻ")]
    assert len(units) == 4  # emoji — ikkita surrogat
    assert (wi.VK_SHIFT, 0, 0) in ev and (wi.VK_RETURN, 0, 0) in ev  # \n → Shift+Enter


def test_combo_events_release_in_reverse():
    ev = wi.combo_events([wi.VK_CONTROL, wi.VK_SHIFT], 0x25)
    assert [vk for vk, _, _ in ev] == [wi.VK_CONTROL, wi.VK_SHIFT, 0x25, 0x25, wi.VK_SHIFT, wi.VK_CONTROL]
    assert ev[2][2] & wi.KEYEVENTF_EXTENDEDKEY  # o'q klavishi — kengaytirilgan


@pytest.mark.skipif(sys.platform != "win32", reason="wintypes.LONG faqat Windows'da 4 bayt")
def test_input_struct_size_matches_win64():
    import ctypes

    assert ctypes.sizeof(wi.INPUT) == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)


@pytest.mark.parametrize(
    ("cmd", "verdict"),
    [
        ("dir", "allow"),
        ("DIR.EXE C:\\Users\\me\\Desktop", "allow"),
        ('dir "C:\\Users\\me\\My Docs"', "allow"),
        ("ipconfig /all", "allow"),
        ("ping -n 3 google.com", "allow"),
        ("ping -t google.com", "deny"),
        ("ping -n 50 google.com", "deny"),
        ("date /t", "allow"),
        ("date", "deny"),
        ("git status", "allow"),
        ("git fetch", "confirm"),
        ("git push", "deny"),
        ("copy a.txt b.txt", "allow"),
        ("copy /y a.txt b.txt", "confirm"),
        ("notepad", "confirm"),
        ("del C:\\x.txt", "deny"),
        ("RD /s /q C:\\x", "deny"),
        ("powershell -c whoami", "deny"),
        ("format C:", "deny"),
        ("echo %USERNAME%", "deny"),
        ("echo a ^& calc", "deny"),
        ("echo a & calc", "deny"),
        ("type C:\\Windows\\System32\\drivers\\etc\\hosts", "deny"),
        ("dir \\\\server\\share", "deny"),
        ("findstr del x.txt", "deny"),
    ],
)
def test_windows_command_guard(cmd, verdict):
    assert wa.WindowsCommandGuard().check(cmd)[0] == verdict


def test_windows_guard_argv_keeps_backslashes():
    assert wa.WindowsCommandGuard.argv('DIR "C:\\My Docs" /b') == ["dir", "C:\\My Docs", "/b"]


async def test_terminal_runs_through_cmd_utf8(monkeypatch):
    calls: list[list[str]] = []

    async def fake_shell(argv, timeout=15.0, stdin=None):
        calls.append(argv)
        return True, "salom"

    monkeypatch.setattr(wa, "run_shell", fake_shell)
    monkeypatch.setattr(wa.settings, "allow_terminal", True)
    c = wa.WindowsController()
    ok, out = await c.run_terminal_command('dir "C:\\My Docs"')
    assert ok and out == "salom"
    assert calls[0][:4] == ["cmd", "/d", "/s", "/c"]
    assert calls[0][4] == 'chcp 65001>nul & dir "C:\\My Docs"'
    ok, out = await c.run_terminal_command("git fetch")
    assert not ok and "Tasdiq" in out and len(calls) == 1
    ok, _ = await c.run_terminal_command("git fetch", confirmed=True)
    assert ok and len(calls) == 2


async def test_type_text_and_hotkey_use_sendinput(monkeypatch):
    sent: list[list] = []
    monkeypatch.setattr(wi, "send_events", lambda ev, chunk=200: sent.append(ev) or len(ev))
    c = wa.WindowsController()
    ok, out = await c.type_text("ok", press_enter=True)
    assert ok and "Enter" in out and len(sent) == 2
    ok, out = await c.press_hotkey("ctrl+s")
    assert ok and len(sent) == 3
    ok, out = await c.press_hotkey("ctrl+")
    assert not ok and len(sent) == 3
