"""Model qaysi toolni tanlashini real Gemini Live sessiyasida o'lchash (toollar BAJARILMAYDI).

    .venv/bin/python scripts/benchmark_live.py                 # 24 ta o'zbekcha buyruq
    .venv/bin/python scripts/benchmark_live.py --group fayl    # faqat bitta guruh
    .venv/bin/python scripts/benchmark_live.py --json out.json # natija fayli

Har bir buyruq alohida sessiyada matn sifatida yuboriladi; modelning tool chaqiruvlariga
stub javob (`{"ok": true, "output": "(benchmark stub)"}`) qaytariladi — mashinaga tegilmaydi.

receive() semantikasi muhim: tool chaqiruvi bilan tugagan navbatdan keyin modelning javobi
KEYINGI navbatda keladi, shuning uchun tool'siz navbat tugaguncha o'qishda davom etamiz.
`nexus.gemini_live_client` o'rniga SDK to'g'ridan-to'g'ri ishlatiladi (soddaroq, mustaqil).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_TURNS = 12
CASE_TIMEOUT_S = 75.0
STUB = {"ok": True, "output": "(benchmark stub)"}

# (buyruq, qabul qilinadigan variantlar — har biri "hammasi chaqirilishi kerak" to'plami, guruh)
CASES: list[tuple[str, list[set[str]], str]] = [
    ("Excelga yoz: Ali, Toshkent, 250 ming", [{"append_spreadsheet_row"}], "fayl"),
    ("Shuni yozib qo'y: ertaga soat uchda uchrashuv", [{"write_note"}], "fayl"),
    ("B7 katakka besh yuz yoz", [{"set_spreadsheet_cell"}], "fayl"),
    ("Jadvalda nima bor?", [{"read_spreadsheet"}], "fayl"),
    ("hisobot.txt fayl yarat va ichiga salom yoz", [{"write_file"}], "fayl"),
    ("notes.txt faylni o'qib ber", [{"read_file"}], "fayl"),
    ("notes.txt ni o'chirib yubor", [{"delete_file"}], "fayl"),
    ("Ish stolida nima bor?", [{"list_directory"}], "fayl"),
    ("Telegramni och", [{"launch_app"}], "dastur"),
    ("Qaysi dasturlar o'rnatilgan?", [{"list_applications"}], "dastur"),
    ("Hujjatlar papkasini och", [{"open_folder"}, {"open_path"}], "dastur"),
    ("Hozir qaysi dasturlar ishlayapti?", [{"list_running_apps"}], "dastur"),
    ("Yozib ber: hurmatli mijoz, buyurtmangiz tayyor", [{"type_text"}], "boshqaruv"),
    ("Saqlab qo'y", [{"press_hotkey"}, {"menu_command"}], "boshqaruv"),
    ("Yangi tugmasini bos", [{"click_ui_element"}], "boshqaruv"),
    ("Fayl menyusida nimalar bor?", [{"list_menus"}], "boshqaruv"),
    ("Ekranda nima yozilgan?", [{"read_screen_text"}, {"list_ui_elements"}], "boshqaruv"),
    ("Ekranni rasmga olib saqlab qo'y", [{"take_screenshot"}], "boshqaruv"),
    ("Batareya necha foiz?", [{"get_system_info"}], "tizim"),
    ("Diskda qancha bo'sh joy bor?", [{"run_terminal_command"}, {"get_system_info"}], "tizim"),
    (
        "Google'da Toshkent ob-havosini qidir va ayt",
        [{"web_search", "browser_read_page"}, {"web_search", "read_screen_text"}, {"web_search", "search_get_results"}],
        "veb",
    ),
    ("Bu sahifada nima yozilgan?", [{"browser_read_page"}, {"read_screen_text"}], "veb"),
    ("Saytdagi Mijozlar bo'limiga o't", [{"browser_click_button"}, {"click_ui_element"}], "veb"),
    ("youtube.com ni och", [{"browser_open_url"}, {"open_path"}], "veb"),
]


def all_declarations() -> list[dict]:
    """Asosiy sxemalar + kengaytma modullari (nomlar bo'yicha takrorsiz)."""
    from nexus.tools.schemas import ALL_TOOL_DECLARATIONS

    decls: dict[str, dict] = {d["name"]: d for d in ALL_TOOL_DECLARATIONS}
    for mod_name in ("nexus.file_actions", "nexus.ax_actions"):
        try:
            mod = __import__(mod_name, fromlist=["TOOL_DECLARATIONS"])
        except Exception as e:  # noqa: BLE001
            print(f"  ! {mod_name} yuklanmadi: {e}")
            continue
        for d in getattr(mod, "TOOL_DECLARATIONS", []):
            decls.setdefault(d["name"], d)
    return list(decls.values())


def build_config(decls: list[dict]) -> object:
    from google.genai import types

    from nexus.tools.schemas import SYSTEM_INSTRUCTION

    fds = [types.FunctionDeclaration(**d) for d in decls]
    return types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[types.Tool(function_declarations=fds)],
    )


async def run_case(client: object, model: str, cfg: object, text: str) -> tuple[list[dict], str, int]:
    """Bitta buyruq: (chaqirilgan toollar [{name,args}], aytilgan matn, navbatlar soni)."""
    from google.genai import types

    called: list[dict] = []
    said: list[str] = []
    turns = 0
    async with client.aio.live.connect(model=model, config=cfg) as session:  # type: ignore[attr-defined]
        await session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text=text)]), turn_complete=True
        )
        for _ in range(MAX_TURNS):
            turns += 1
            used_tool = False
            async for message in session.receive():
                if message.tool_call:
                    used_tool = True
                    replies = []
                    for call in message.tool_call.function_calls or []:
                        called.append({"name": call.name, "args": dict(call.args or {})})
                        replies.append(types.FunctionResponse(id=call.id, name=call.name, response=dict(STUB)))
                    await session.send_tool_response(function_responses=replies)
                sc = message.server_content
                if sc and sc.output_transcription and sc.output_transcription.text:
                    said.append(sc.output_transcription.text)
                if sc and sc.turn_complete:
                    break
            if not used_tool:
                break  # tool'siz navbat — ish tugadi
    return called, "".join(said).strip(), turns


def passed(expected: list[set[str]], called: list[str]) -> bool:
    got = set(called)
    return any(alt <= got for alt in expected)


async def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Nexus tool tanlash benchmarki (Gemini Live)")
    p.add_argument("--group", help="faqat shu guruh: fayl|dastur|boshqaruv|tizim|veb")
    p.add_argument("--limit", type=int, default=0, help="faqat birinchi N ta buyruq")
    p.add_argument("--model", help="Model nomi (standart: GEMINI_MODEL)")
    p.add_argument("--json", default=None, help="Natija JSON fayli (standart: benchmark_<vaqt>.json)")
    args = p.parse_args(argv)


    from nexus.config import settings

    if not settings.gemini_api_key.strip():
        print("GEMINI_API_KEY yo'q (.env). Benchmark real API talab qiladi.")
        return 2
    model = args.model or settings.gemini_model
    decls = all_declarations()
    cfg = build_config(decls)
    client = settings.make_client()

    cases = [c for c in CASES if not args.group or c[2] == args.group]
    if args.limit:
        cases = cases[: args.limit]
    print(f"\nModel: {model}   toollar: {len(decls)}   buyruqlar: {len(cases)}\n")
    print(f"  {'':5s} {'Buyruq':46s} {'Chaqirilgan toollar':40s} {'ms':>6s}")
    print("  " + "-" * 100)

    rows: list[dict] = []
    for text, expected, group in cases:
        started = time.monotonic()
        try:
            called, said, turns = await asyncio.wait_for(run_case(client, model, cfg, text), timeout=CASE_TIMEOUT_S)
            error = None
        except Exception as e:  # noqa: BLE001
            called, said, turns, error = [], "", 0, f"{type(e).__name__}: {str(e)[:120]}"
        ms = int((time.monotonic() - started) * 1000)
        names = [c["name"] for c in called]
        ok = error is None and passed(expected, names)
        flag = "OK " if ok else "XATO"
        shown = ", ".join(names)[:40] if names else (error or "—")
        loop_note = "  <- ko'p" if len(names) > 4 else ""
        print(f"  {flag:5s} {text[:46]:46s} {shown:40s} {ms:6d}{loop_note}")
        rows.append(
            {
                "text": text,
                "group": group,
                "expected": [sorted(a) for a in expected],
                "called": called,
                "said": said,
                "turns": turns,
                "ms": ms,
                "ok": ok,
                "error": error,
            }
        )

    by_group: dict[str, list[bool]] = {}
    for r in rows:
        by_group.setdefault(r["group"], []).append(r["ok"])
    total = len(rows)
    good = sum(r["ok"] for r in rows)
    spoke = sum(1 for r in rows if r["said"])
    calls = [len(r["called"]) for r in rows]
    print("\n  Guruhlar:")
    for g, res in by_group.items():
        print(f"    {g:10s} {sum(res)}/{len(res)}")
    print(f"\n  JAMI: {good}/{total} = {100 * good / max(total, 1):.0f}%")
    print(f"  gapirgan: {spoke}/{total}")
    if calls:
        print(f"  chaqiruvlar: o'rtacha {sum(calls) / len(calls):.1f}, eng ko'pi {max(calls)}")
    print(f"  o'rtacha vaqt: {sum(r['ms'] for r in rows) / max(total, 1):.0f} ms")

    out = Path(args.json or f"benchmark_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}.json")
    out.write_text(
        json.dumps(
            {
                "model": model,
                "date": datetime.now().astimezone().isoformat(timespec="seconds"),
                "tools": len(decls),
                "passed": good,
                "total": total,
                "by_group": {g: [sum(v), len(v)] for g, v in by_group.items()},
                "cases": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"  JSON: {out}\n")
    return 0 if good == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
