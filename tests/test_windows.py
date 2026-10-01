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
    from nexus.windows_browser import WindowsBrowser

    assert isinstance(reg.tabs, WindowsBrowser) and reg.youtube is reg.tabs and reg.search_input is reg.tabs
    assert wa.SUPPORTED_TOOLS <= names
    assert "set_brightness" not in names and "browser_click_selector" not in names
    assert reg.extensions == list(wa.WINDOWS_EXTENSION_MODULES)
    # ekran toollari macOS modullaridan emas, windows_screen'dan
    assert {"read_screen_text", "click_ui_element", "look_at_screen"} <= names
    assert "UI Automation" in next(d for d in reg.declarations() if d["name"] == "read_screen_text")["description"]


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


# ---------------------------------------------------------------------------
# 2-bosqich: ekran (UI Automation) — soxta boshqaruv elementlari bilan
# ---------------------------------------------------------------------------
from types import SimpleNamespace

from nexus import windows_screen as ws


def _ctrl(role, name, rect=(10, 20, 110, 60), offscreen=False, **kw):
    left, top, right, bottom = rect
    return SimpleNamespace(
        ControlTypeName=role,
        Name=name,
        IsOffscreen=offscreen,
        BoundingRectangle=SimpleNamespace(left=left, top=top, right=right, bottom=bottom),
        HelpText=kw.get("help", ""),
        AutomationId="",
        GetValuePattern=lambda: SimpleNamespace(Value=kw["value"]) if "value" in kw else None,
        GetTextPattern=lambda: None,
    )


def test_collect_elements_filters_and_dedupes():
    controls = [
        _ctrl("ButtonControl", "Saqlash"),
        _ctrl("ButtonControl", "Saqlash"),  # dublikat
        _ctrl("ButtonControl", "Yashirin", offscreen=True),
        _ctrl("TextControl", "Faqat matn"),
        _ctrl("ButtonControl", ""),
        _ctrl("EditControl", "", help="Qidiruv"),
        _ctrl("HyperlinkControl", "Bekor", rect=(0, 0, 0, 0)),  # o'lchamsiz
    ]
    els = ws.collect_elements(controls)
    assert [(e.index, e.role, e.name) for e in els] == [(1, "ButtonControl", "Saqlash"), (2, "EditControl", "Qidiruv")]
    assert els[0].center == (60, 40)
    assert els[0].as_dict() == {"n": 1, "role": "tugma", "label": "Saqlash", "x": 60, "y": 40}
    assert [e.name for e in ws.collect_elements(controls, "qidir")] == ["Qidiruv"]


def test_find_by_label_priority():
    els = ws.collect_elements(
        [_ctrl("ButtonControl", n, rect=(i, 0, i + 10, 10)) for i, n in enumerate(["Save as", "Save", "Autosave"])]
    )
    assert [e.name for e in ws.find_by_label(els, "save")] == ["Save"]
    assert [e.name for e in ws.find_by_label(els, "sav")] == ["Save as", "Save"]
    assert [e.name for e in ws.find_by_label(els, "uto")] == ["Autosave"]
    assert ws.find_by_label(els, "  ") == []


def test_collect_text_uses_values_and_limit():
    controls = [
        _ctrl("TitleBarControl", "Hujjat - Notepad"),
        _ctrl("EditControl", "Matn tahriri", value="Salom dunyo"),
        _ctrl("TextControl", "Salom dunyo"),  # takror
        _ctrl("ButtonControl", "Yopish", offscreen=True),
    ]
    assert ws.collect_text(controls) == "Hujjat - Notepad\nSalom dunyo\nMatn tahriri"
    assert len(ws.collect_text(controls, limit=10)) == 10


async def test_screen_tools_refuse_off_windows(monkeypatch):
    monkeypatch.setattr(ws.sys, "platform", "darwin")
    res = await ws.read_screen_text({})
    assert not res["ok"] and "Windows" in res["output"]


async def test_read_screen_text_falls_back_to_ocr(monkeypatch):
    monkeypatch.setattr(ws.sys, "platform", "win32")
    monkeypatch.setattr(ws, "_text_sync", lambda limit: ("Telegram", ""))

    async def fake_gemini(prompt):
        return {"ok": True, "output": "ekrandagi matn"}

    monkeypatch.setattr(ws, "_ask_gemini", fake_gemini)
    res = await ws.read_screen_text({})
    assert res["ok"] and res["source"] == "ocr" and res["output"] == "ekrandagi matn"


def test_windows_screen_declarations_have_handlers():
    assert {d["name"] for d in ws.TOOL_DECLARATIONS} == set(ws.HANDLERS)


# ---------------------------------------------------------------------------
# 2-bosqich: brauzer
# ---------------------------------------------------------------------------
from nexus import windows_browser as wb


def _bw(proc, title, hwnd=1):
    return wb.BrowserWindow(hwnd, proc, title)


def test_browser_key_and_pick_window():
    wins = [_bw("msedge", "Bing - Microsoft\u200b Edge", 1), _bw("chrome", "YouTube - Google Chrome", 2)]
    assert wb.browser_key("Google Chrome") == "chrome" and wb.browser_key("safari") is None
    assert wb.pick_window(wins, "chrome").hwnd == 2
    assert wb.pick_window(wins, "").hwnd == 1  # eng ustidagi istalgan brauzer
    assert wb.pick_window(wins, "firefox").hwnd == 1  # so'ralgan yo'q — istalgani
    assert wb.pick_window([], "chrome") is None
    assert wins[0].page_title == "Bing" and wins[1].page_title == "YouTube" and wins[0].label == "Edge"


@pytest.mark.parametrize(
    ("secs", "presses"),
    [(30, [("l", 3)]), (-10, [("j", 1)]), (15, [("l", 1), ("right", 1)]), (5, [("right", 1)]), (0, [])],
)
def test_seek_presses(secs, presses):
    assert wb.seek_presses(secs) == presses


def test_speed_presses():
    assert wb.speed_presses(1.0) == [("shift+,", 8), ("shift+.", 3)]
    assert wb.speed_presses(0.1) == [("shift+,", 8)]
    assert wb.speed_presses(5) == [("shift+,", 8), ("shift+.", 7)]


def test_looks_like_result():
    assert wb.looks_like_result("Python dasturlash tili — Vikipediya")
    assert not wb.looks_like_result("Images")
    assert not wb.looks_like_result("3")
    assert not wb.looks_like_result("https://example.com/some/long/path")


@pytest.fixture
def browser(monkeypatch):
    b = wb.WindowsBrowser()
    sent: list[tuple] = []

    async def fake_window(browser):
        return _bw("chrome", "Lofi beats - YouTube - Google Chrome", 7)

    async def fake_keys(browser, *combos):
        sent.extend(combos)
        return _bw("chrome", "x", 7), ""

    async def fake_playing(browser):
        return True

    monkeypatch.setattr(b, "_window", fake_window)
    monkeypatch.setattr(b, "_keys", fake_keys)
    monkeypatch.setattr(b, "_is_playing", fake_playing)
    return b, sent


async def test_youtube_uses_player_keys(browser):
    b, sent = browser
    assert (await b.toggle_play(""))[0] and sent[-1] == ("k", 1)
    ok, out = await b.play("")  # allaqachon ijroda — klavish bosilmaydi
    assert ok and "allaqachon" in out and len(sent) == 1
    assert (await b.pause(""))[0] and sent[-1] == ("k", 1)
    await b.seek("", -25)
    assert sent[-2:] == [("j", 2), ("left", 1)]
    await b.set_player_volume("", 30)
    assert sent[-2:] == [("down", 20), ("up", 6)]
    await b.next_video("")
    assert sent[-1] == ("shift+n", 1)


async def test_youtube_refuses_non_youtube_tab(browser, monkeypatch):
    b, sent = browser

    async def other(browser):
        return _bw("chrome", "Gmail - Google Chrome", 7)

    monkeypatch.setattr(b, "_window", other)
    ok, out = await b.toggle_play("")
    assert not ok and "YouTube emas" in out and sent == []


async def test_browser_scroll_and_tabs_keys(browser):
    b, sent = browser
    await b.scroll_page("", "down", 1200)
    assert sent[-1] == ("pagedown", 2)
    await b.close_current_tab("")
    assert sent[-1] == ("ctrl+w", 1)
    ok, _out = await b.scroll_page("", "sideways")
    assert not ok


def test_windows_declarations_adapted(monkeypatch):
    monkeypatch.setattr(reg_mod, "IS_WINDOWS", True)
    reg = reg_mod.ToolRegistry(None, None)
    decls = {d["name"]: d for d in reg.declarations()}
    assert decls["browser_scroll"]["parameters"]["properties"]["browser"]["enum"] == ["chrome", "edge", "firefox"]
    assert "Safari" not in decls["browser_open_url"]["description"]
    assert "browser_click_selector" not in decls
    # macOS deklaratsiyalari o'zgarmagan (nusxa olingan)
    assert {d["name"]: d for d in ALL_TOOL_DECLARATIONS}["browser_scroll"]["parameters"]["properties"]["browser"]["enum"] == [
        "safari",
        "chrome",
    ]


# ---------------------------------------------------------------------------
# 2-bosqich: video tarjima (Nexus WebView2 oynasida)
# ---------------------------------------------------------------------------
from nexus import video_translate as vt
from nexus import windows_video as wv


async def test_video_host_requires_gui(monkeypatch):
    monkeypatch.setattr(wv, "_gui_ready", wv.threading.Event())
    ok, out = await wv.WebViewVideoHost().open("https://youtu.be/x")
    assert not ok and "desktop" in out


async def test_video_host_eval_without_window():
    ok, out = await wv.WebViewVideoHost().eval("1+1")
    assert not ok and "yopilgan" in out


async def test_video_host_eval_returns_string(monkeypatch):
    host = wv.WebViewVideoHost()
    host.window = SimpleNamespace(evaluate_js=lambda js: '{"t": 1.5}')
    assert await host.eval("x") == (True, '{"t": 1.5}')
    host.window = SimpleNamespace(evaluate_js=lambda js: None)
    assert await host.eval("x") == (True, "")


async def test_translator_js_goes_to_webview_on_windows(monkeypatch):
    calls: list[str] = []

    async def fake_eval(js):
        calls.append(js)
        return True, "ok"

    monkeypatch.setattr(vt, "IS_WINDOWS", True)
    monkeypatch.setattr(wv.host, "eval", fake_eval)
    assert await vt.VideoTranslator()._js("return 1") == (True, "ok")
    assert calls == ["return 1"]


def test_translate_video_decl_on_windows():
    decl = next(d for d in vt.TOOL_DECLARATIONS if d["name"] == "translate_video")
    out = wa.adapt_declaration(decl)
    assert "browser" not in out["parameters"]["properties"]
    assert "Nexus video window" in out["description"]
    assert "browser" in decl["parameters"]["properties"]  # asl nusxa o'zgarmagan


def test_video_install_hint_and_no_window_flags(monkeypatch):
    assert ("winget" in vt.INSTALL_HINT) == (sys.platform == "win32")
    assert ("creationflags" in vt.NO_WINDOW) == (sys.platform == "win32")


def test_page_title_strips_profile():
    assert _bw("msedge", "Sahifa - Profile 1 - Microsoft\u200b Edge").page_title == "Sahifa"


def test_pick_page_document_prefers_title_and_skips_browser_ui():
    def doc(name, cls=""):
        return SimpleNamespace(ControlTypeName="DocumentControl", Name=name, ClassName=cls)

    docs = [doc("", "WebView"), doc("Welcome"), doc("Mening sahifam"), doc("", "HubWebView")]
    assert wb.pick_page_document(docs, [50, 30, 10, 40], "Mening sahifam") == 2
    assert wb.pick_page_document(docs, [50, 30, 10, 40], "") == 1  # eng kattasi, UI emas
    assert wb.pick_page_document(docs, [50, 2, 2, 40], "") is None  # hammasi bo'sh yoki UI


def test_document_tree_retries_until_filled(monkeypatch):
    import nexus.windows_screen as wscreen

    page = SimpleNamespace(ControlTypeName="DocumentControl", Name="Sahifa", ClassName="")
    btn = SimpleNamespace(ControlTypeName="ButtonControl")
    calls = {"n": 0}

    def fake_walk(root, max_items=4000):
        if root is page:
            calls["n"] += 1
            return [page] if calls["n"] < 3 else [page, btn, btn, btn]
        return [root, page]

    monkeypatch.setattr(wscreen, "_walk", fake_walk)
    monkeypatch.setattr(wb, "DOC_RETRY_S", 0)
    items = wb.document_tree(SimpleNamespace(ControlTypeName="PaneControl"), "Sahifa")
    assert len(items) == 4 and calls["n"] == 3
