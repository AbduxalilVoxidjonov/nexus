"""Windows: pywebview (WebView2) oynasida JS bajarish — video tarjima kanali ishlayaptimi.

    uv run python scripts/windows_webview_smoke.py
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Video smoke</title></head>
<body><video id="v" muted></video><script>document.getElementById('v').currentTime = 0;</script></body></html>"""

result: dict[str, object] = {}


def check() -> None:
    import webview

    from nexus import video_translate as vt
    from nexus import windows_video as wv

    async def run() -> None:
        page = Path(tempfile.gettempdir()) / "nexus_video_smoke.html"
        page.write_text(PAGE, encoding="utf-8")
        ok, out = await wv.host.open(page.as_uri())
        result["open"] = (ok, out)
        state = (False, "")
        for _ in range(20):
            await asyncio.sleep(0.5)
            state = await wv.host.eval(vt._STATE_JS)
            if state[0] and state[1].startswith("{"):
                break
        result["state"] = state
        result["parsed"] = vt.parse_player_state(state[1]) if state[0] else None

    wv.mark_gui_ready()
    try:
        asyncio.run(run())
    finally:
        for w in list(webview.windows):
            w.destroy()


def main() -> int:
    import webview

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    webview.create_window("Nexus smoke", html="<p>asosiy</p>", width=300, height=200)
    webview.start(check)
    print("open :", result.get("open"))
    print("state:", result.get("state"))
    print("parsed:", result.get("parsed"))
    ok = bool(result.get("state") and result["state"][0] and result.get("parsed") is not None)
    print("[OK] evaluate_js orqali video holati o'qildi" if ok else "[XATO] video holati o'qilmadi")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
