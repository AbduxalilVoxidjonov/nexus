"""Windows smoke testi: registry, xavfsiz toollar va UI serveri haqiqiy Windows'da ishlaydimi.

    uv run python scripts/windows_smoke.py

Ovoz/ekran/oynalarga ta'sir qiladigan toollar (ovoz, qulflash, media) chaqirilmaydi.
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

failures: list[str] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    print(f"[{'OK' if ok else 'XATO'}] {name}: {str(detail)[:200]}")
    if not ok:
        failures.append(name)


def soft(name: str, ok: bool, detail: object = "") -> None:
    """Muhitga bog'liq tekshiruv (brauzerning birinchi ishga tushishi va h.k.) — build'ni to'xtatmaydi."""
    print(f"[{'OK' if ok else '..'}] {name}: {str(detail)[:300]}")


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Nexus Smoke Sahifa</title></head>
<body><h1>Salom, Nexus brauzer testi</h1><p>Bu sahifa smoke test uchun yaratilgan matn.</p>
<button onclick="document.title='Bosildi OK'">Bosing</button>
<input aria-label="Qidiruv" placeholder="Qidiruv"></body></html>"""


async def browser_smoke(reg, probe_dir: Path) -> None:
    page = probe_dir / "nexus_smoke.html"
    page.write_text(PAGE, encoding="utf-8")
    # Har bir buyruq — foydalanuvchining yangi gapi: oldingi navbatda o'qilgan tashqi matn (taint)
    # keyingi amallarga tasdiq talab qilmasin
    reg.new_turn()
    res = await reg.execute("browser_open_url", {"url": page.as_uri()})
    soft("browser_open_url", res.get("ok"), res.get("output"))
    await asyncio.sleep(6)  # brauzer ochilishi
    for tool, args in (
        ("browser_current_page", {}),
        ("browser_list_tabs", {}),
        ("browser_read_page", {}),
        ("browser_click_button", {"button_text": "Bosing"}),
    ):
        reg.new_turn()
        res = await reg.execute(tool, args)
        soft(tool, res.get("ok"), res.get("output") or res.get("error"))
        await asyncio.sleep(1)
    reg.new_turn()
    res = await reg.execute("browser_current_page", {})
    soft("tugma bosilgandan keyin sarlavha", "Bosildi OK" in (res.get("output") or ""), res.get("output"))
    reg.new_turn()
    res = await reg.execute("browser_close_tab", {})
    soft("browser_close_tab", res.get("ok"), res.get("output"))


async def main() -> int:
    assert sys.platform == "win32", "Bu skript faqat Windows uchun"
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from nexus.config import settings
    from nexus.tools.registry import ToolRegistry
    from nexus.windows_actions import SUPPORTED_TOOLS, WindowsController

    reg = ToolRegistry(None, settings)
    names = {d["name"] for d in reg.declarations()}
    check("registry WindowsController", isinstance(reg.mac, WindowsController), type(reg.mac).__name__)
    core = {n for n in names if n in SUPPORTED_TOOLS}
    check("asosiy toollar e'lon qilingan", core == SUPPORTED_TOOLS, sorted(SUPPORTED_TOOLS - core))
    check("macOS-only toollar yashirin", "set_brightness" not in names and "browser_click_selector" not in names, len(names))
    check("file_actions yuklangan", "nexus.file_actions" in reg.extensions, reg.extensions)

    m = reg.mac
    info = await m.get_system_info()
    check("get_system_info", info.get("cpu_percent") is not None, info.get("summary"))
    check("list_applications", *(await m.list_applications()))
    check("list_running_apps", *(await m.list_running_apps()))
    check("frontmost_app", *(await m.frontmost_app()))

    marker = "Nexus smoke o'zbekcha ✓"
    ok, out = await m.set_clipboard(marker)
    check("set_clipboard", ok, out)
    ok, out = await m.get_clipboard()
    check("get_clipboard (UTF-8)", ok and out.strip() == marker, out)

    shot = Path(tempfile.gettempdir()) / "nexus_smoke.png"
    ok, out = await m.take_screenshot(str(shot))
    # CI'da (sessiyasiz runner) ekran bo'lmasligi mumkin — faqat ogohlantiramiz
    print(f"[{'OK' if ok else '..'}] take_screenshot: {out[:200]}")

    probe_dir = Path.home() / "nexus_smoke"
    probe_dir.mkdir(exist_ok=True)
    (probe_dir / "hisobot_smoke.txt").write_text("salom", encoding="utf-8")
    res = await reg.execute("find_files", {"query": "hisobot_smoke", "folder": str(probe_dir)})
    check("find_files (os.walk)", res.get("ok") and "hisobot_smoke.txt" in res.get("output", ""), res.get("output"))

    # --- 2-bosqich: terminal ---
    ok, out = await m.run_terminal_command("echo salom dunyo")
    check("terminal: echo", ok and "salom dunyo" in out, out)
    ok, out = await m.run_terminal_command(f'dir "{probe_dir}"')
    check("terminal: dir (bo'shliqli yo'l)", ok and "hisobot_smoke.txt" in out, out)
    ok, out = await m.run_terminal_command("del C:\\x.txt")
    check("terminal: del rad etiladi", not ok and "rad" in out, out)
    ok, out = await m.run_terminal_command("echo %USERNAME%")
    check("terminal: %VAR% rad etiladi", not ok, out)

    # --- 2-bosqich: klaviatura (Notepad'ga terib, bufer orqali qaytarib o'qiymiz) ---
    import subprocess

    notepad = subprocess.Popen(["notepad.exe"])  # noqa: ASYNC220 — smoke skript
    try:
        await asyncio.sleep(2.5)
        typed = "Salom, oʻzbekcha gʻ va кирилл!"
        ok, out = await m.type_text(typed)
        check("type_text", ok, out)
        await asyncio.sleep(0.5)
        ok1, _ = await m.press_hotkey("ctrl+a")
        ok2, _ = await m.press_hotkey("cmd+c")  # macOS yozuvi → Ctrl+C
        await asyncio.sleep(0.5)
        ok, out = await m.get_clipboard()
        check("type_text + hotkey (Notepad orqali)", ok1 and ok2 and out.strip() == typed, out)

        # --- 2-bosqich: ekran (UI Automation) — Notepad hali ochiq ---
        res = await reg.execute("read_screen_text", {})
        check("read_screen_text (UIA)", res.get("ok") and "кирилл" in res.get("output", ""), res.get("output"))
        res = await reg.execute("list_ui_elements", {})
        check("list_ui_elements", res.get("ok") and '"count": 0' not in res.get("output", ""), res.get("output"))
        res = await reg.execute("get_focused_element", {})
        check("get_focused_element", res.get("ok"), res.get("output"))
        from nexus.windows_screen import capture_window_jpeg

        jpeg, app = await asyncio.to_thread(capture_window_jpeg)
        check("oyna skrinshoti (Pillow)", jpeg[:2] == b"\xff\xd8" and len(jpeg) > 1000, f"{app}: {len(jpeg)} bayt")
    finally:
        notepad.kill()
    ok, out = await m.press_hotkey("ctrl+nokey")
    check("press_hotkey: noma'lum klavish xatosi", not ok and "Noma'lum" in out, out)

    await browser_smoke(reg, probe_dir)

    from fastapi.testclient import TestClient

    from nexus.events import bus
    from nexus.server import create_app

    with TestClient(create_app(bus, settings)) as client:
        r = client.get("/")
        check("UI index.html", r.status_code == 200 and "<html" in r.text.lower(), r.status_code)

    print("\n" + ("Hammasi joyida." if not failures else f"{len(failures)} ta xato: {failures}"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
