"""Nexus dastlabki tekshiruvi: kalit, audio, ruxsatlar, (ixtiyoriy) Gemini Live ping.

    .venv/bin/python scripts/check_setup.py            # kalit + audio + ruxsatlar + mikrofon 2s
    .venv/bin/python scripts/check_setup.py --live     # + Gemini Live sessiyasi ("Say OK")
    .venv/bin/python scripts/check_setup.py --no-mic   # mikrofonga yozmasdan

API kaliti hech qachon chop etilmaydi — faqat "bor/yo'q" va uzunligi.
"""

from __future__ import annotations

import argparse
import asyncio
import ctypes
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OK = "\033[32m✓\033[0m"
BAD = "\033[31m✗\033[0m"
WARN = "\033[33m!\033[0m"


def line(ok: bool | None, text: str) -> None:
    mark = OK if ok else (WARN if ok is None else BAD)
    print(f"  [{mark}] {text}")


# ---------------------------------------------------------------------------
# Tekshiruvlar
# ---------------------------------------------------------------------------
def check_python() -> bool:
    v = sys.version_info
    ok = v >= (3, 11)
    line(ok, f"Python {v.major}.{v.minor}.{v.micro} ({sys.executable})")
    return ok


def check_key() -> bool:
    from nexus.config import settings

    key = (settings.gemini_api_key or "").strip()
    if key:
        line(True, f"GEMINI_API_KEY bor (uzunligi {len(key)} belgi)")
        line(True, f"Model: {settings.gemini_model}  |  Ovoz: {settings.gemini_voice}")
        return True
    line(False, "GEMINI_API_KEY yo'q — .env.example nusxasini .env qilib kalitni yozing")
    return False


def check_packages() -> bool:
    ok = True
    for mod, hint in (
        ("google.genai", "google-genai"),
        ("sounddevice", "sounddevice"),
        ("openpyxl", "openpyxl (Excel toollari)"),
        ("ApplicationServices", "pyobjc-framework-ApplicationServices (AX toollari)"),
        ("Quartz", "pyobjc-framework-Quartz (klik)"),
        ("AppKit", "pyobjc-framework-Cocoa"),
    ):
        try:
            __import__(mod)
            line(True, f"Paket: {hint}")
        except Exception as e:  # noqa: BLE001
            line(False, f"Paket yo'q: {hint} — {type(e).__name__}")
            ok = False
    return ok


def check_devices() -> bool:
    try:
        import sounddevice as sd

        inp = sd.query_devices(kind="input")
        out = sd.query_devices(kind="output")
        line(True, f"Mikrofon (standart): {inp['name']}  ({int(inp['default_samplerate'])} Hz)")
        line(True, f"Dinamik  (standart): {out['name']}")
        n_in = sum(1 for d in sd.query_devices() if d.get("max_input_channels", 0) > 0)
        line(True, f"Kirish qurilmalari: {n_in} ta")
        return True
    except Exception as e:  # noqa: BLE001
        line(False, f"Audio qurilma topilmadi: {type(e).__name__}: {e}")
        return False


def check_mic_level(seconds: float = 2.0) -> bool:
    try:
        import numpy as np
        import sounddevice as sd

        rate = int(sd.query_devices(kind="input")["default_samplerate"])
        print(f"\n  {seconds:.0f} soniya davomida gapiring ...")
        rec = sd.rec(int(seconds * rate), samplerate=rate, channels=1, dtype="int16")
        sd.wait()
    except Exception as e:  # noqa: BLE001
        line(False, f"Mikrofondan yozib bo'lmadi: {type(e).__name__}: {e}")
        line(None, "Privacy & Security → Microphone → Terminal (yoki Python) ga ruxsat bering")
        return False
    samples = rec.astype(np.float32)
    rms = float(np.sqrt(np.mean(samples**2)))
    peak = int(np.max(np.abs(rec)))
    if peak < 200:
        line(False, f"Ovoz eshitilmadi (RMS={rms:.0f}, peak={peak}) — mikrofon ruxsati yoki qurilma noto'g'ri")
        return False
    line(True, f"Mikrofon ishlayapti (RMS={rms:.0f}, peak={peak})")
    return True


def _load(path: str) -> ctypes.CDLL | None:
    try:
        return ctypes.cdll.LoadLibrary(path)
    except OSError:
        return None


def check_accessibility() -> bool:
    lib = _load("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
    if lib is None:
        line(None, "Accessibility tekshirib bo'lmadi")
        return False
    lib.AXIsProcessTrusted.restype = ctypes.c_bool
    ok = bool(lib.AXIsProcessTrusted())
    if ok:
        line(True, "Accessibility ruxsati bor (klik, matn terish, AX toollari)")
    else:
        line(False, "Accessibility yo'q: Privacy & Security → Accessibility → Terminal/Python ni yoqing")
    return ok


def check_screen_recording() -> bool:
    lib = _load("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    if lib is None:
        line(None, "Screen Recording tekshirib bo'lmadi")
        return False
    lib.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
    ok = bool(lib.CGPreflightScreenCaptureAccess())
    if ok:
        line(True, "Screen Recording ruxsati bor (skrinshot)")
    else:
        line(False, "Screen Recording yo'q: Privacy & Security → Screen & System Audio Recording")
    return ok


def check_automation() -> bool:
    try:
        proc = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to get name of first process'],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        line(False, f"Automation tekshiruvi bajarilmadi: {e}")
        return False
    if proc.returncode == 0:
        line(True, "Automation (System Events) ruxsati bor")
        return True
    err = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "xato"
    line(False, f"Automation yo'q: Privacy & Security → Automation → System Events ({err})")
    return False


async def check_live(timeout: float = 15.0) -> bool:
    from google.genai import types

    from nexus.config import settings

    client = settings.make_client()
    cfg = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )
    reply: list[str] = []
    audio_bytes = 0
    started = time.monotonic()

    async def _session() -> None:
        nonlocal audio_bytes
        async with client.aio.live.connect(model=settings.gemini_model, config=cfg) as session:
            await session.send_client_content(
                turns=types.Content(role="user", parts=[types.Part(text="Say OK")]), turn_complete=True
            )
            async for message in session.receive():
                sc = message.server_content
                if sc is None:
                    continue
                if sc.model_turn:
                    for part in sc.model_turn.parts or []:
                        if part.inline_data and part.inline_data.data:
                            audio_bytes += len(part.inline_data.data)
                if sc.output_transcription and sc.output_transcription.text:
                    reply.append(sc.output_transcription.text)
                if sc.turn_complete:
                    break

    try:
        await asyncio.wait_for(_session(), timeout=timeout)
    except TimeoutError:
        line(False, f"Gemini Live: {timeout:.0f}s ichida javob kelmadi")
        return False
    except Exception as e:  # noqa: BLE001
        line(False, f"Gemini Live ulanmadi: {type(e).__name__}: {str(e)[:160]}")
        return False
    ms = int((time.monotonic() - started) * 1000)
    if audio_bytes == 0 and not reply:
        line(False, f"Gemini Live ulandi, lekin audio kelmadi ({ms} ms)")
        return False
    line(True, f"Gemini Live javob berdi: {''.join(reply).strip()!r}, audio {audio_bytes // 1024} KB, {ms} ms")
    return True


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Nexus sozlamalarini tekshirish")
    p.add_argument("--live", action="store_true", help="Gemini Live sessiyasini ham sinash")
    p.add_argument("--no-mic", action="store_true", help="Mikrofonga yozmaslik")
    p.add_argument("--seconds", type=float, default=2.0, help="Mikrofon yozish davomiyligi (s)")
    args = p.parse_args(argv)

    print("\nNexus Ovoz OS — sozlamalar tekshiruvi\n" + "=" * 44)
    results: dict[str, bool] = {}

    print("\nMuhit")
    results["python"] = check_python()
    results["paketlar"] = check_packages()
    results["kalit"] = check_key()

    print("\nAudio")
    results["audio"] = check_devices()

    print("\nmacOS ruxsatlari")
    results["accessibility"] = check_accessibility()
    results["screen_recording"] = check_screen_recording()
    results["automation"] = check_automation()

    if args.live:
        print("\nGemini Live")
        if results["kalit"]:
            results["live"] = asyncio.run(check_live())
        else:
            line(False, "Kalit yo'q — Live tekshiruvi o'tkazib yuborildi")
            results["live"] = False

    if not args.no_mic and results["audio"]:
        print("\nMikrofon")
        results["mikrofon"] = check_mic_level(args.seconds)

    failed = [k for k, v in results.items() if not v]
    print("\n" + "=" * 44)
    if not failed:
        print("  Hammasi joyida. Ishga tushirish:  .venv/bin/nexus  yoki  .venv/bin/python -m nexus.main")
        return 0
    print(f"  Muammolar: {', '.join(failed)}. Yuqoridagi ✗ qatorlarni tuzating.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
