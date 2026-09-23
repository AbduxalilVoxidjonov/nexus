"""Gemini ovozlarini o'zbekcha namunaviy jumla bilan tinglab tanlash.

    .venv/bin/python scripts/voice_picker.py                     # qisqa ro'yxat (10 ta iliq ovoz)
    .venv/bin/python scripts/voice_picker.py --all               # barcha 30 ta ovoz
    .venv/bin/python scripts/voice_picker.py --voices Aoede,Kore # tanlab
    .venv/bin/python scripts/voice_picker.py --play              # yozib, darhol eshittirish
    .venv/bin/python scripts/voice_picker.py --say "O'z matningiz"

Har ovoz uchun WAV (24 kHz, mono, 16-bit) `voice_samples/` papkasiga yoziladi.
Yoqqanini `.env` ga yozing:  GEMINI_VOICE=<nomi>
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Barcha 30 ta tayyor ovoz va Google bergan xarakteri
ALL_VOICES: dict[str, str] = {
    "Aoede": "breezy",
    "Autonoe": "bright",
    "Despina": "smooth",
    "Zubenelgenubi": "casual",
    "Sulafat": "warm",
    "Vindemiatrix": "gentle",
    "Achird": "friendly",
    "Callirrhoe": "easy-going",
    "Leda": "youthful",
    "Achernar": "soft",
    "Algieba": "smooth",
    "Kore": "firm",
    "Puck": "upbeat",
    "Charon": "informative",
    "Fenrir": "excitable",
    "Zephyr": "bright",
    "Orus": "firm",
    "Enceladus": "breathy",
    "Iapetus": "clear",
    "Umbriel": "easy-going",
    "Algenib": "gravelly",
    "Rasalgethi": "informative",
    "Laomedeia": "upbeat",
    "Alnilam": "firm",
    "Schedar": "even",
    "Gacrux": "mature",
    "Pulcherrima": "forward",
    "Erinome": "clear",
    "Sadachbia": "lively",
    "Sadaltager": "knowledgeable",
}

# Iliq, xotirjam, suhbat ohangi — uy yordamchisi uchun mos
SHORTLIST = [
    "Aoede",
    "Sulafat",
    "Vindemiatrix",
    "Achird",
    "Despina",
    "Callirrhoe",
    "Leda",
    "Achernar",
    "Algieba",
    "Zubenelgenubi",
]

SAMPLE_TEXT = (
    "Assalomu alaykum! Men Nexus — sizning ovozli yordamchingizman. "
    "Ertaga soat o'nda uchrashuv bor, eslatib turaman. Yana nima qilay?"
)
SAMPLE_RATE = 24_000
OUT_DIR = ROOT / "voice_samples"


def save_wav(path: Path, pcm: bytes, rate: int = SAMPLE_RATE) -> None:
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(rate)
        fh.writeframes(pcm)


async def render(client: object, model: str, voice: str, text: str, timeout: float = 40.0) -> bytes:
    from google.genai import types

    cfg = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice))
        ),
        system_instruction=(
            "You are a warm, calm voice assistant speaking Uzbek. Read the user's text back exactly as "
            "written, naturally and unhurried. Add nothing."
        ),
    )
    chunks: list[bytes] = []

    async def _session() -> None:
        async with client.aio.live.connect(model=model, config=cfg) as session:  # type: ignore[attr-defined]
            await session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text=text)]), turn_complete=True
            )
            for _ in range(3):
                done = False
                async for message in session.receive():
                    sc = message.server_content
                    if sc and sc.model_turn:
                        for part in sc.model_turn.parts or []:
                            if part.inline_data and part.inline_data.data:
                                chunks.append(part.inline_data.data)
                    if sc and sc.turn_complete:
                        done = True
                        break
                if done:
                    break

    await asyncio.wait_for(_session(), timeout=timeout)
    return b"".join(chunks)


async def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Gemini ovozlarini o'zbekcha tinglash")
    p.add_argument("--all", action="store_true", help="barcha 30 ta ovoz")
    p.add_argument("--voices", help="vergul bilan ajratilgan ovoz nomlari, masalan Aoede,Kore")
    p.add_argument("--say", default=SAMPLE_TEXT, help="o'qiladigan matn")
    p.add_argument("--play", action="store_true", help="yozilgach afplay bilan eshittirish")
    p.add_argument("--out", default=str(OUT_DIR), help="WAV fayllar papkasi")
    p.add_argument("--model", help="Model nomi (standart: GEMINI_MODEL)")
    args = p.parse_args(argv)


    from nexus.config import settings

    if not settings.gemini_api_key.strip():
        print("GEMINI_API_KEY yo'q (.env).")
        return 2

    if args.voices:
        chosen = []
        for raw in args.voices.split(","):
            name = raw.strip()
            match = next((v for v in ALL_VOICES if v.lower() == name.lower()), None)
            if match is None:
                print(f"Noma'lum ovoz: {name}. Mavjud: {', '.join(ALL_VOICES)}")
                return 2
            chosen.append(match)
    else:
        chosen = list(ALL_VOICES) if args.all else SHORTLIST

    model = args.model or settings.gemini_model
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    client = settings.make_client()

    print(f"\nModel: {model}   ovozlar: {len(chosen)}   papka: {out_dir}\n")
    written: list[Path] = []
    for i, voice in enumerate(chosen, 1):
        print(f"  [{i:2d}/{len(chosen)}] {voice:14s} ({ALL_VOICES.get(voice, '?'):13s}) ...", end=" ", flush=True)
        try:
            pcm = await render(client, model, voice, args.say)
        except Exception as e:  # noqa: BLE001
            print(f"xato: {type(e).__name__}: {str(e)[:80]}")
            continue
        if not pcm:
            print("audio kelmadi")
            continue
        path = out_dir / f"{i:02d}-{voice}.wav"
        save_wav(path, pcm)
        written.append(path)
        print(f"{len(pcm) / (SAMPLE_RATE * 2):.1f}s -> {path.name}")
        if args.play and sys.platform == "darwin":
            proc = await asyncio.create_subprocess_exec("afplay", str(path))
            await proc.wait()

    print(f"\n  {len(written)} ta namuna: {out_dir}")
    print("  Yoqqanini .env ga yozing:  GEMINI_VOICE=<nomi>\n")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
