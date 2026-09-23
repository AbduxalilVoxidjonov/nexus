"""nexus.server (FastAPI + WS ko'prigi) testlari."""

from __future__ import annotations

import asyncio
import json
import socket
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from nexus.config import Settings
from nexus.events import EventBus
from nexus.server import UI_DIR, UIServer, create_app


@pytest.fixture
def bus() -> EventBus:
    b = EventBus()
    b.publish("TRANSCRIPT", {"role": "user", "text": "salom", "final": True})
    b.publish("METRICS", {"cpu": 12.5, "ram": 40.0, "battery": 88, "latency_ms": 210})
    b.set_state("listening")

    async def get_state(msg: dict[str, Any]) -> dict[str, Any]:
        return {"state": b.state, "snapshot": b.snapshot, "history": b.history()}

    async def echo(msg: dict[str, Any]) -> dict[str, Any]:
        return {"echo": msg.get("value")}

    b.register_command("get_state", get_state)
    b.register_command("text", echo)
    return b


@pytest.fixture
def client(bus: EventBus) -> TestClient:
    app = create_app(bus, Settings())
    return TestClient(app)


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "state": "listening"}


def test_api_state(client: TestClient) -> None:
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "listening"
    assert body["snapshot"]["METRICS"]["cpu"] == 12.5
    assert [e["type"] for e in body["history"]] == ["TRANSCRIPT"]


def test_index_serves_ui(client: TestClient) -> None:
    assert (UI_DIR / "index.html").is_file()
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "NEXUS OVOZ OS" in r.text
    css = client.get("/static/styles.css")
    assert css.status_code == 200
    js = client.get("/static/app.js")
    assert js.status_code == 200


def test_index_disabled_when_serve_ui_false(bus: EventBus) -> None:
    app = create_app(bus, Settings(serve_ui=False))
    with TestClient(app) as c:
        assert c.get("/").status_code == 404
        assert c.get("/health").status_code == 200


def test_ws_hello_and_commands(client: TestClient, bus: EventBus) -> None:
    with client.websocket_connect("/ws") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "HELLO"
        assert hello["data"]["state"] == "listening"
        assert hello["data"]["snapshot"]["METRICS"]["latency_ms"] == 210
        assert hello["data"]["history"][0]["data"]["text"] == "salom"

        ws.send_json({"cmd": "get_state", "reqId": 7})
        res = ws.receive_json()
        assert res["type"] == "CMD_RESULT"
        assert res["reqId"] == 7
        assert res["data"]["ok"] is True
        assert res["data"]["state"] == "listening"
        assert "snapshot" in res["data"] and "history" in res["data"]

        ws.send_json({"cmd": "text", "value": "salom dunyo", "reqId": "abc"})
        res = ws.receive_json()
        assert res["reqId"] == "abc"
        assert res["data"] == {"ok": True, "cmd": "text", "echo": "salom dunyo"}

        ws.send_json({"cmd": "nope"})
        res = ws.receive_json()
        assert res["data"]["ok"] is False
        assert "Noma'lum buyruq" in res["data"]["error"]
        assert res["reqId"] is None

        ws.send_text("{bu json emas")
        res = ws.receive_json()
        assert res["data"]["ok"] is False


def test_ws_slow_command_does_not_block_following_commands() -> None:
    """Tasdiq kutayotgan run_tool shu soketdan keladigan "confirm" ni to'sib qo'ymasligi kerak."""
    b = EventBus()
    release = asyncio.Event()

    async def slow(msg: dict[str, Any]) -> dict[str, Any]:
        await asyncio.wait_for(release.wait(), timeout=5)
        return {"slow": True}

    async def unblock(msg: dict[str, Any]) -> dict[str, Any]:
        release.set()
        return {"released": True}

    b.register_command("slow", slow)
    b.register_command("unblock", unblock)
    with TestClient(create_app(b, Settings())) as c, c.websocket_connect("/ws") as ws:
        ws.receive_json()  # HELLO
        ws.send_json({"cmd": "slow", "reqId": 1})
        ws.send_json({"cmd": "unblock", "reqId": 2})
        results = {r["reqId"]: r["data"] for r in (ws.receive_json(), ws.receive_json())}
        assert results[2] == {"ok": True, "cmd": "unblock", "released": True}
        assert results[1] == {"ok": True, "cmd": "slow", "slow": True}


def test_ws_get_state_without_handler() -> None:
    b = EventBus()
    b.set_state("processing")
    with TestClient(create_app(b, Settings())) as c, c.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_json({"cmd": "get_state"})
        res = ws.receive_json()
        assert res["data"]["ok"] is True
        assert res["data"]["state"] == "processing"


def test_ws_receives_published_events(bus: EventBus) -> None:
    app = create_app(bus, Settings())

    async def trigger(msg: dict[str, Any]) -> dict[str, Any]:
        bus.bind_loop()
        bus.publish(
            "TOOL_CALLED",
            {"name": "open_app", "args": {"name": "Safari"}, "duration_ms": 12, "ok": True, "output": ""},
        )
        return {}

    bus.register_command("trigger", trigger)
    with TestClient(app) as c, c.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_json({"cmd": "trigger"})
        got = [ws.receive_json(), ws.receive_json()]
        types = sorted(m["type"] for m in got)
        assert types == ["CMD_RESULT", "TOOL_CALLED"]
        ev = next(m for m in got if m["type"] == "TOOL_CALLED")
        assert ev["data"]["name"] == "open_app"
        assert ev["data"]["args"] == {"name": "Safari"}


def test_multiple_clients_and_unsubscribe(bus: EventBus) -> None:
    app = create_app(bus, Settings())
    with TestClient(app) as c:
        with c.websocket_connect("/ws") as a, c.websocket_connect("/ws") as b2:
            assert a.receive_json()["type"] == "HELLO"
            assert b2.receive_json()["type"] == "HELLO"
            # 2 ta client + 1 ta tasdiq kuzatuvchisi (_ConfirmTracker)
            assert len(app.state.clients) == 2
            assert len(bus._subscribers) == 3
        # Ikkalasi uzilgach client obunalari tozalanadi (asinxron yopilishga ozgina vaqt)
        for _ in range(50):
            if len(bus._subscribers) <= 1:
                break
            time.sleep(0.02)
        assert len(app.state.clients) == 0
        assert len(bus._subscribers) == 1


def test_confirm_request_push_and_confirm_cmd(bus: EventBus) -> None:
    app = create_app(bus, Settings())
    received: list[dict[str, Any]] = []

    async def confirm(msg: dict[str, Any]) -> dict[str, Any]:
        received.append(msg)
        bus.publish(
            "CONFIRM_RESOLVED",
            {"token": msg["token"], "approved": bool(msg["approve"]), "source": "ui"},
        )
        return {"token": msg["token"], "approved": bool(msg["approve"])}

    async def ask(msg: dict[str, Any]) -> dict[str, Any]:
        bus.bind_loop()
        bus.publish(
            "CONFIRM_REQUEST",
            {
                "token": "t1",
                "action": "delete_file",
                "summary": "~/Desktop/a.txt o'chirish",
                "reason": "qaytarib bo'lmaydi",
                "ttl_s": 30,
            },
        )
        return {}

    bus.register_command("confirm", confirm)
    bus.register_command("ask", ask)

    with TestClient(app) as c:
        with c.websocket_connect("/ws") as ws:
            hello = ws.receive_json()
            assert hello["data"]["pending_confirm"] is None
            ws.send_json({"cmd": "ask"})
            got = [ws.receive_json(), ws.receive_json()]
            req = next(m for m in got if m["type"] == "CONFIRM_REQUEST")
            assert req["data"]["token"] == "t1"
            assert req["data"]["ttl_s"] == 30

            # Yangi ulangan client HELLO'da ochiq tasdiqni ko'radi
            with c.websocket_connect("/ws") as ws2:
                hello2 = ws2.receive_json()
                pc = hello2["data"]["pending_confirm"]
                assert pc is not None and pc["token"] == "t1" and pc["action"] == "delete_file"

            ws.send_json({"cmd": "confirm", "token": "t1", "approve": True, "reqId": 5})
            got = [ws.receive_json(), ws.receive_json()]
            res = next(m for m in got if m["type"] == "CMD_RESULT")
            assert res["reqId"] == 5 and res["data"]["ok"] is True and res["data"]["approved"] is True
            resolved = next(m for m in got if m["type"] == "CONFIRM_RESOLVED")
            assert resolved["data"] == {"token": "t1", "approved": True, "source": "ui"}
            assert received[0]["approve"] is True

            with c.websocket_connect("/ws") as ws3:
                assert ws3.receive_json()["data"]["pending_confirm"] is None
        assert c.get("/api/state").json()["pending_confirm"] is None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def test_uiserver_start_stop() -> None:
    b = EventBus()
    b.bind_loop()
    port = _free_port()
    ui = UIServer(b, Settings(ui_host="127.0.0.1", ui_port=port))
    await ui.start()
    try:
        assert ui._task is not None and not ui._task.done()
        # Oddiy HTTP so'rov (asyncio streams orqali, qo'shimcha kutubxonasiz)
        for _ in range(30):
            try:
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                break
            except OSError:
                await asyncio.sleep(0.05)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        await writer.drain()
        raw = await asyncio.wait_for(reader.read(), timeout=3)
        writer.close()
        head, _, body = raw.partition(b"\r\n\r\n")
        assert b"200" in head.split(b"\r\n")[0]
        assert json.loads(body) == {"ok": True, "state": "idle"}
    finally:
        await ui.stop()
    assert ui._task is None


async def test_uiserver_port_busy_raises() -> None:
    b = EventBus()
    b.bind_loop()
    port = _free_port()
    blocker = socket.socket()
    blocker.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    blocker.bind(("127.0.0.1", port))
    blocker.listen(1)
    try:
        ui = UIServer(b, Settings(ui_host="127.0.0.1", ui_port=port))
        with pytest.raises(OSError):
            await ui.start()
        assert ui._task is None
    finally:
        blocker.close()


# ---------------------------------------------------------------------------
# ui/app.js — "Qayta ulanish": faqat bitta jonli WebSocket qolishi kerak (identity tekshiruvi)
# ---------------------------------------------------------------------------
def test_app_js_manual_reconnect_keeps_single_socket() -> None:
    import shutil
    import subprocess
    from pathlib import Path

    node = shutil.which("node")
    if node is None:
        pytest.skip("node topilmadi")
    harness = Path(__file__).parent / "js" / "ws_reconnect_harness.js"
    subprocess.run([node, "--check", str(UI_DIR / "app.js")], check=True)
    proc = subprocess.run(
        [node, str(harness), str(UI_DIR / "app.js")], capture_output=True, text=True, timeout=30, check=False
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout.strip().splitlines()[-1])
    assert out["first_open"] is True
    assert out["old_closed_called"] is True  # eski soket yopilgan
    # Eski soketning kech kelgan onclose'i yangi reconnect rejalashtirmasin: jami 2 ta, jonli 1 ta
    assert out["sockets_total"] == 2, out
    assert out["live"] == 1, out
    assert out["current_is_second"] is True and out["ws_open"] is True
