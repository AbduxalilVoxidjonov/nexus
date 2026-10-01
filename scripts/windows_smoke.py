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


async def main() -> int:
    assert sys.platform == "win32", "Bu skript faqat Windows uchun"
    from nexus.config import settings
    from nexus.tools.registry import ToolRegistry
    from nexus.windows_actions import SUPPORTED_TOOLS, WindowsController

    reg = ToolRegistry(None, settings)
    names = {d["name"] for d in reg.declarations()}
    check("registry WindowsController", isinstance(reg.mac, WindowsController), type(reg.mac).__name__)
    core = {n for n in names if n in SUPPORTED_TOOLS}
    check("asosiy toollar e'lon qilingan", core == SUPPORTED_TOOLS, sorted(SUPPORTED_TOOLS - core))
    check("macOS-only toollar yashirin", "set_brightness" not in names and "type_text" not in names, len(names))
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

    res = await reg.execute("find_files", {"query": "nexus", "folder": str(ROOT)})
    check("find_files (os.walk)", res.get("ok"), res.get("output"))

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
