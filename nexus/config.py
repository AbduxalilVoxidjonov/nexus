"""Markaziy konfiguratsiya (.env / muhit o'zgaruvchilaridan o'qiladi).

Modul yuklanganda `.env` manbalari shu tartibda o'qiladi (mavjud muhit o'zgaruvchilari ustun,
`override=False`): joriy papka `.env` → `~/.nexus/.env` → (.app ichida) `Contents/Resources/.env`.
Shuning uchun `settings` singleton'i ham, keyin qurilgan `Settings()` ham bir xil qiymatni ko'radi.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# GEMINI_API_KEY uchun "kalit yo'q" deb hisoblanadigan namunaviy qiymatlar (.env.example, start.command)
API_KEY_PLACEHOLDERS = frozenset({"your_api_key_here", "sizning_api_key", "sizning_api_kalitingiz", "changeme"})


def _project_env() -> Path | None:
    """Loyiha ildizidagi `.env` (`nexus/config.py` ga nisbatan) — boshqa papkadan ishga tushirilganda ham."""
    if getattr(sys, "frozen", False):
        return None
    return Path(__file__).resolve().parent.parent / ".env"


def env_candidates() -> list[Path]:
    """`.env` manbalari, ustuvorlik tartibida (birinchisi ustun):

    1. joriy papkadan yuqoriga qarab topilgan `.env` (avvalgi `load_dotenv()` xatti-harakati);
    2. loyiha ildizidagi `.env`;
    3. `~/.nexus/.env` — .app (PyInstaller) yoki boshqa papkadan ishga tushirilganda;
    4. `<Nexus.app>/Contents/Resources/.env` va `Contents/MacOS/.env` — bundle ichiga qo'yilgan nusxa.
    """
    candidates: list[Path] = []
    found = find_dotenv(usecwd=True)
    if found:
        candidates.append(Path(found))
    proj = _project_env()
    if proj is not None:
        candidates.append(proj)
    candidates.append(Path("~/.nexus/.env").expanduser())
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        candidates.append(exe.parent.parent / "Resources" / ".env")  # Contents/MacOS/.. → Contents/Resources
        candidates.append(exe.parent / ".env")
    uniq: list[Path] = []
    for c in candidates:
        if c not in uniq:
            uniq.append(c)
    return uniq


def load_env_files() -> list[Path]:
    """Barcha `.env` manbalarini `override=False` bilan yuklaydi; yuklanganlarini qaytaradi."""
    loaded: list[Path] = []
    for path in env_candidates():
        try:
            if path.is_file() and load_dotenv(path, override=False):
                loaded.append(path)
        except OSError:
            continue
    return loaded


def load_extra_env() -> list[Path]:
    """Faqat qo'shimcha manbalar (`~/.nexus/.env`, .app bundle) — loyiha `.env` isiz. Mos kelish uchun."""
    home = Path("~/.nexus/.env").expanduser()
    cands = env_candidates()
    loaded: list[Path] = []
    for path in cands[cands.index(home):]:
        try:
            if path.is_file() and load_dotenv(path, override=False):
                loaded.append(path)
        except OSError:
            continue
    return loaded


load_env_files()


def _env_api_key(name: str = "GEMINI_API_KEY") -> str:
    """Kalit; namunaviy (placeholder) qiymat bo'lsa bo'sh qaytaradi."""
    v = (os.getenv(name) or "").strip()
    return "" if is_placeholder_api_key(v) else v


def is_placeholder_api_key(value: str | None) -> bool:
    v = (value or "").strip().strip("\"'").lower()
    return not v or v in API_KEY_PLACEHOLDERS or v.startswith(("your_", "sizning_"))


# API kalit belgilari: Google kalitlari (AIza...) harf/raqam, `-`, `_`; boshqa formatlar uchun `.`, `~`, `+`,
# `/`, `=` ham ruxsat. `#`, `$`, qo'shtirnoq, `\\`, bo'shliq va yangi qator YO'Q — `.env` ga qator/izoh qo'shib bo'lmasin.
_API_KEY_RE = re.compile(r"^[A-Za-z0-9._~+/=\-]{20,300}$")
_ENV_KEY_LINE = re.compile(r"^[ \t]*(export[ \t]+)?GEMINI_API_KEY[ \t]*=", re.MULTILINE)
# Nusxa olishda qo'shilib qoladigan ko'rinmas belgilar (zero-width, BOM, NBSP, yo'nalish belgilari)
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00a0\u202f\u200e\u200f\u202a\u202c"), None)
_QUOTES = "\"'`“”„‘’‚«»"
_KEY_PREFIX = re.compile(r"^(export\s+)?(GEMINI_API_KEY|GOOGLE_API_KEY|API_KEY)\s*[=:]\s*", re.IGNORECASE)


def _describe_char(c: str) -> str:
    if c in "\r\n":
        return "yangi qator"
    if c.isspace():
        return "bo'sh joy"
    if c in _QUOTES:
        return f"qo'shtirnoq ({c})"
    return f"'{c}'" if c.isprintable() and ord(c) < 128 else f"maxsus belgi U+{ord(c):04X}"


def validate_api_key(value: str | None) -> str:
    """UI dan kiritilgan kalitni tozalaydi va tekshiradi; yaroqsiz bo'lsa `ValueError`.

    Nusxa olishda qo'shilgan narsalar avtomatik olib tashlanadi: ko'rinmas belgilar, chetdagi bo'shliq va
    qo'shtirnoqlar, `GEMINI_API_KEY=` prefiksi. Xato xabarida kalitning o'zi ko'rsatilmaydi."""
    v = (value or "").translate(_INVISIBLE).strip()
    v = _KEY_PREFIX.sub("", v).strip().strip(_QUOTES).strip()
    if is_placeholder_api_key(v):
        raise ValueError("API kalit bo'sh yoki namunaviy qiymat")
    if not _API_KEY_RE.match(v):
        bad = next((i for i, c in enumerate(v) if not _API_KEY_RE.match("a" * 20 + c)), None)
        if bad is not None:
            raise ValueError(
                f"API kalitda ruxsat etilmagan belgi bor: {_describe_char(v[bad])}, {bad + 1}-o'rinda "
                f"(jami {len(v)} belgi). Kalitni aistudio.google.com/apikey dan qayta nusxa oling"
            )
        raise ValueError(f"API kalit juda {'qisqa' if len(v) < 20 else 'uzun'} ({len(v)} belgi) — to'liq nusxa olinganini tekshiring")
    return v


def api_key_hint(key: str | None) -> str:
    """UI uchun niqoblangan ko'rinish: `AIza…x1y2` (kalitning o'zi hech qachon UI ga yuborilmaydi)."""
    k = (key or "").strip()
    if not k:
        return ""
    return f"{k[:4]}…{k[-4:]}" if len(k) > 12 else "…" + k[-2:]


def api_key_env_path() -> Path:
    """UI dan kiritilgan kalit yoziladigan `.env`.

    `.env` fayllari `override=False` bilan yuklanadi — birinchi aniqlangan qiymat yutadi. Shuning uchun
    kalit `~/.nexus/.env` dan ustun turgan (cwd/loyiha) faylda allaqachon yozilgan bo'lsa (namunaviy
    qiymat bo'lsa ham) — o'sha faylni yangilaymiz, aks holda keyingi ishga tushishda eski qiymat yutadi.
    Boshqa hollarda — `~/.nexus/.env` (.app bundle ichidagi fayl o'zgartirilmaydi)."""
    home = Path("~/.nexus/.env").expanduser()
    for path in env_candidates():
        if path == home:
            break
        try:
            if path.is_file() and os.access(path, os.W_OK) and _ENV_KEY_LINE.search(path.read_text(encoding="utf-8")):
                return path
        except (OSError, UnicodeDecodeError):
            continue
    return home


def save_api_key(key: str, path: Path | None = None) -> Path:
    """`GEMINI_API_KEY=` qatorini `.env` da yangilaydi (bo'lmasa qo'shadi), faylni 0600 qiladi va
    joriy jarayon muhitini ham yangilaydi. Yozilgan fayl yo'lini qaytaradi."""
    key = validate_api_key(key)
    target = path or api_key_env_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        text = ""
    line = f"GEMINI_API_KEY={key}"
    out: list[str] = []
    replaced = False
    for ln in text.splitlines():
        if _ENV_KEY_LINE.match(ln):
            if not replaced:
                out.append(line)
                replaced = True
            continue  # takroriy qatorlar olib tashlanadi
        out.append(ln)
    if not replaced:
        out.append(line)
    tmp = target.with_name(target.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    os.replace(tmp, target)
    os.chmod(target, 0o600)
    os.environ["GEMINI_API_KEY"] = key
    return target


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    # Gemini
    gemini_api_key: str = field(default_factory=_env_api_key)
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.8-live"))
    # Matnli (Interactions API) model — web_answer tool uchun
    gemini_text_model: str = field(default_factory=lambda: os.getenv("GEMINI_TEXT_MODEL", "gemini-3.8-flash"))
    # low|medium|high (bo'sh = berilmaydi; "extended-thinking" modelida talab qilinadi)
    thinking_level: str = field(default_factory=lambda: os.getenv("GEMINI_THINKING_LEVEL", "").strip().lower())
    # Live sessiyada Google Search grounding
    google_search_grounding: bool = field(default_factory=lambda: _env_bool("GOOGLE_SEARCH_GROUNDING", False))
    # Live API versiyasi: v1alpha (BidiGenerateContent) yoki v1beta
    gemini_api_version: str = field(default_factory=lambda: os.getenv("GEMINI_API_VERSION", "v1alpha").strip() or "v1alpha")

    def make_client(self):
        """google-genai Client — hamma joyda bir xil sozlama bilan."""
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=self.gemini_api_key,
            http_options=types.HttpOptions(api_version=self.gemini_api_version),
        )
    gemini_voice: str = field(default_factory=lambda: os.getenv("GEMINI_VOICE", "Aoede"))
    assistant_language: str = field(default_factory=lambda: os.getenv("ASSISTANT_LANGUAGE", "uz"))

    # Audio
    input_sample_rate: int = field(default_factory=lambda: _env_int("INPUT_SAMPLE_RATE", 16000))
    output_sample_rate: int = field(default_factory=lambda: _env_int("OUTPUT_SAMPLE_RATE", 24000))
    chunk_ms: int = field(default_factory=lambda: _env_int("AUDIO_CHUNK_MS", 20))
    input_device: str | None = field(default_factory=lambda: os.getenv("INPUT_DEVICE") or None)
    playback_enabled: bool = field(default_factory=lambda: _env_bool("PLAYBACK_ENABLED", True))
    vad_threshold: float = field(default_factory=lambda: _env_float("VAD_THRESHOLD", 0.02))
    # Yordamchi gapirayotganda mikrofon chunklarini bostirish (o'z ovozini eshitmasin)
    echo_guard: bool = field(default_factory=lambda: _env_bool("ECHO_GUARD", True))
    # Javob paytida gapirsa yordamchi to'xtasinmi (barge-in). False (standart) — bitta buyruq oxirigacha:
    # buyruq bajarilib javob aytilguncha mikrofon to'liq bostiriladi (bu vaqtdagi gap navbatga ham tushmaydi),
    # server ham javobni uzmaydi (NO_INTERRUPTION); tugagach yordamchi "Yana nima qilay?" deb so'raydi.
    allow_interrupt: bool = field(default_factory=lambda: _env_bool("ALLOW_INTERRUPT", False))
    # Ijro paytida foydalanuvchi gapirsa (barge-in) — RMS bo'sag'aning necha barobaridan oshsa o'tkaziladi
    echo_barge_factor: float = field(default_factory=lambda: _env_float("ECHO_BARGE_FACTOR", 3.0))
    # Barge-in ochilishi uchun uzluksiz baland ovoz davomiyligi (ms) — qisqa echo cho'qqisi javobni uzmasin
    echo_barge_min_ms: int = field(default_factory=lambda: _env_int("ECHO_BARGE_MIN_MS", 160))
    # Barge-in ochilgach oxirgi baland chunkdan keyin ham shuncha ochiq turadi (ms)
    echo_barge_hold_ms: int = field(default_factory=lambda: _env_int("ECHO_BARGE_HOLD_MS", 600))
    # Ijrodan oldin yig'iladigan jitter-bufer (ms)
    playback_prebuffer_ms: int = field(default_factory=lambda: _env_int("PLAYBACK_PREBUFFER_MS", 220))
    # Chiqish oqimi latency'si: "high" (barqaror, chirsillamaydi) | "low" | sekund (masalan 0.08)
    playback_latency: str = field(default_factory=lambda: os.getenv("PLAYBACK_LATENCY", "high"))

    # Gemini server-VAD (LOW/HIGH)
    vad_start_sensitivity: str = field(default_factory=lambda: os.getenv("VAD_START_SENSITIVITY", "LOW"))
    vad_end_sensitivity: str = field(default_factory=lambda: os.getenv("VAD_END_SENSITIVITY", "HIGH"))
    vad_prefix_ms: int = field(default_factory=lambda: _env_int("VAD_PREFIX_MS", 150))
    vad_silence_ms: int = field(default_factory=lambda: _env_int("VAD_SILENCE_MS", 500))
    # Kiruvchi transkripsiya tillari (vergul bilan). Bo'sh = avtomatik.
    transcription_languages: str = field(
        default_factory=lambda: os.getenv("TRANSCRIPTION_LANGUAGES", "uz-UZ,ru-RU,en-US")
    )
    # Sessiyani davom ettirish (resume handle) va kontekst siqish
    session_resumption: bool = field(default_factory=lambda: _env_bool("SESSION_RESUMPTION", True))
    context_compression: bool = field(default_factory=lambda: _env_bool("CONTEXT_COMPRESSION", True))

    # Ism bilan chaqirish (wake): always | name | smart
    wake_name: str = field(default_factory=lambda: os.getenv("WAKE_NAME", "Nexus"))
    wake_mode: str = field(default_factory=lambda: os.getenv("WAKE_MODE", "name"))
    wake_follow_up_s: float = field(default_factory=lambda: _env_float("WAKE_FOLLOW_UP_S", 8.0))
    # Suhbat rejimi ("kel gaplashamiz"): shuncha soniya jimlikdan keyin o'zi tugaydi
    conversation_idle_s: float = field(default_factory=lambda: _env_float("CONVERSATION_IDLE_S", 45.0))

    # UI ko'prigi
    ui_host: str = field(default_factory=lambda: os.getenv("UI_HOST", "127.0.0.1"))
    ui_port: int = field(default_factory=lambda: _env_int("UI_PORT", 8765))
    serve_ui: bool = field(default_factory=lambda: _env_bool("SERVE_UI", True))

    # Qayta ulanish
    reconnect_base_delay: float = field(default_factory=lambda: _env_float("RECONNECT_BASE_DELAY", 1.0))
    reconnect_max_delay: float = field(default_factory=lambda: _env_float("RECONNECT_MAX_DELAY", 30.0))

    # Xavfsizlik
    allow_terminal: bool = field(default_factory=lambda: _env_bool("ALLOW_TERMINAL", True))
    # Xavfli amallar (savatni tozalash, faylni o'chirish/ustiga yozish, terminal) oldidan tasdiq so'ralsinmi.
    # False (standart) — buyruq aytilishi bilan bajariladi. Tashqi matn (veb/fayl/ekran) o'qilgan navbatdagi
    # xavfli amal baribir tasdiq so'raydi — bu prompt injection himoyasi, foydalanuvchi buyrug'i emas.
    require_confirmation: bool = field(default_factory=lambda: _env_bool("REQUIRE_CONFIRMATION", False))
    screenshot_dir: Path = field(
        default_factory=lambda: Path(os.getenv("SCREENSHOT_DIR", "~/Desktop")).expanduser()
    )

    # Video tarjimasi (translate_video): model bo'sh = GEMINI_MODEL; rejim prompt|native
    video_translate_model: str = field(default_factory=lambda: os.getenv("VIDEO_TRANSLATE_MODEL", "").strip())
    video_translate_mode: str = field(default_factory=lambda: os.getenv("VIDEO_TRANSLATE_MODE", "prompt").strip())
    # Parallel tarjimon sessiyalari (bittasi band paytda kelgan gaplarni tashlab yuboradi)
    video_translate_sessions: int = field(default_factory=lambda: _env_int("VIDEO_TRANSLATE_SESSIONS", 5))

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    @property
    def transcription_language_list(self) -> list[str]:
        return [x.strip() for x in (self.transcription_languages or "").split(",") if x.strip()]


settings = Settings()
