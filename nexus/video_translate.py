"""YouTube videosini jonli (sinxron) ovozli tarjima: ingliz → o'zbek.

Oqim:
    yt-dlp (audio faylni yuklaydi) ──▶ ffmpeg -ss (16 kHz mono s16le, stdout) ──▶ navbat
    ──▶ alohida Gemini Live sessiyasi (tarjimon) ──▶ o'z AudioPlayer'i (24 kHz) ──▶ dinamik

Video brauzerda ochiladi, audio yuklanguncha pauzada turadi, asl ovozi o'chiriladi (yoki pasaytiriladi).
Audio oldindan yuklanadi: YouTube to'g'ridan-to'g'ri oqimni sekinlashtiradi (~1.7x, 5 s start),
lokal fayldan esa seek bir zumda. Tarjimaga yuboriladigan
audio brauzerdagi `video.currentTime` ga bog'langan (`PlaybackClock`): pauza/reklama → yuborish
to'xtaydi, oldinga/orqaga o'tkazish (seek) → ffmpeg yangi joydan qayta ishga tushadi.

Tarjima — bir nechta parallel Gemini Live sessiyasi (`VIDEO_TRANSLATE_SESSIONS`, standart 5; kalit kvotasi ~5 ta bir vaqtdagi sessiya):
bitta sessiya bir vaqtda faqat bitta javob beradi va band paytda kelgan bo'laklarni tashlab/qisqartirib
yuboradi (sinovda 60 s inglizchadan 20–34 s o'zbekcha, kechikish 8–30 s). Shuning uchun audio `Segmenter`
bilan 2.5–5 s bo'laklarga (gap orasidagi jimroq joyda) bo'linadi, har bir bo'lak bo'sh sessiyaga
(`activity_start` … audio … `activity_end`, server-VAD o'chiq) beriladi, javoblar esa `seq` tartibida
ijro etiladi (`_playout`). Javob bermagan bo'lak boshqa sessiyaga qayta beriladi.
Har bir bo'lak — yangi sessiya: worker oldindan ulanib turadi, faqat yopilgan (to'liq yig'ilgan) bo'lakni
oladi va bir zumda yuboradi. Javob audiosi `generation_complete` gacha to'liq keladi — shu payt bo'lak tayyor
va sessiya yopiladi. (Bitta sessiyada `turn_complete` ~4 s keyin keladi va undan OLDIN yuborilgan yangi
bo'lakka model umuman javob bermaydi — sessiyani qayta ishlatish sekinroq; uzun kontekstda model ham
chalkashib `{"cont": ...}` kabi narsalar aytardi.) Tarjima o'rniga izoh aytilsa — bo'lak qayta yuboriladi.
Dublyaj rejimi: audio fayl oldindan yuklangani uchun tarjimaga videodan `LOOKAHEAD_S` oldinda
yuboriladi; har bir bo'lak videodagi o'z oralig'ini (`src_start`–`src_end`) biladi va video shu joyga
yetganda ijro etiladi. Boshida video birinchi tarjima tayyor bo'lguncha pauzada turadi. O'zbekcha tarjima
inglizchadan ~20% uzun — bo'lak o'z oralig'iga sig'masa ffmpeg `atempo` bilan 1.0–1.35x tezlashtiriladi
(`fit_tempo`); javob hali kelayotgan bo'lsa — kelgan sari oddiy tezlikda oqiziladi. Server javob audiosini ~real vaqtda yuboradi, shuning uchun bo'lak tayyor bo'lishiga
"bo'lak + javob + tarjima uzunligi" ≈ 10–12 s ketadi — `LOOKAHEAD_S` = 15. O'lchovlar (TED, 90 s):
real vaqtda tarjima — o'rtacha kechikish 9.5 s (max 13); 8 s oldinda — 4.0 s (max 6.5, 4 bo'lak
tushdi); 15 s oldinda + 4 sessiya — 0.1 s (max 1.2). Javobsiz bo'lak boshqa sessiyaga qayta beriladi.

Rejim (`VIDEO_TRANSLATE_MODE`): prompt (standart, tarjimon system instruction) | native (+
`translation_config`; gemini-3.8-live da ulanadi, lekin hech narsa qaytarmadi). Video pauza qilinsa
tarjima ijrosi ham to'xtab turadi (`AudioPlayer.hold`).

Asosiy sessiya (mikrofon) karnaydagi tarjimani eshitib qolmasligi uchun `attach()`
`AudioStreamer.extra_playing` ilgagini o'rnatadi (echo guard tarjima ijrosini ham hisobga oladi).

Kengaytma kontrakti (registry): `TOOL_DECLARATIONS: list[dict]`, `HANDLERS: dict[name, async handler]`.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger("nexus.video_translate")

IN_RATE = 16000
CHUNK_S = 0.1
CHUNK_BYTES = int(IN_RATE * CHUNK_S) * 2  # s16le mono
LOOKAHEAD_S = 15.0  # audio videodan shuncha oldinda tarjimaga yuboriladi (tarjima o'z vaqtiga tayyor turadi)
MAX_LATE_S = 6.0  # tarjima o'z oralig'i tugaganidan shuncha kech qolsa — o'tkazib yuboriladi
FIRST_READY_TIMEOUT_S = 15.0  # buferlash (boshida / seek'dan keyin) ko'pi bilan shuncha davom etadi
GATE_AHEAD_S = 3.0  # buferlash: videodan shuncha soniya oldinga tarjima tayyor bo'lguncha video pauzada
RESYNC_S = 3.0  # video va yuborilgan audio farqi bundan oshsa — ffmpeg qayta ishga tushadi
RESYNC_GRACE_S = 1.5  # ffmpeg ishga tushgandan keyin shuncha vaqt resync tekshirilmaydi
POLL_S = 0.5  # brauzerdan pleyer holatini so'rash oralig'i
SEGMENT_MIN_S = 2.5  # bo'lak kamida shuncha — undan keyin jimroq joyda kesiladi
SEGMENT_MAX_S = 5.0  # jimlik topilmasa ham shu uzunlikda kesiladi
DEFAULT_SESSIONS = 5  # parallel tarjimon sessiyalari (har biri bo'lakka ~10 s band: javob + audio + turn_complete)
NO_RESPONSE_S = 4.0  # activity_end dan keyin shuncha vaqtda audio kelmasa — bo'lak boshqa sessiyaga qayta beriladi
MAX_RETRIES = 1  # qayta urinishdan keyin ham javob bo'lmasa — o'tkazib yuboriladi
MAX_TEMPO = 1.3  # tarjima o'z vaqt oralig'iga sig'masa shu tezlikkacha tezlashtiriladi (ohang o'zgarmaydi)
SPILL_S = 0.7  # tarjima o'z oralig'idan shuncha oshib ketishi mumkin (kechikish keyingi pauzada yo'qoladi)
SILENT_RMS = 0.008  # bo'lakning o'rtacha RMS'i bundan past — jimlik, API'ga yuborilmaydi (kvota tejaladi)
WORKER_RELEASE_S = 20.0  # turn_complete kelmasa ham sessiya shundan keyin bo'sh deb hisoblanadi
SEGMENT_QUIET_RATIO = 0.35  # chunk RMS bo'lak o'rtachasining shu qismidan past — "jimlik"
IDLE_END_S = 0.3  # navbat shuncha bo'sh tursa (pauza) ochiq bo'lak yopiladi
DOWNLOAD_TIMEOUT_S = 120.0  # bitta urinish; sekin tarmoqda foydalanuvchi uzoq kutib qolmasin
DOWNLOAD_ATTEMPTS = 3
VIDEO_WAIT_S = 20.0
MAX_SESSION_FAILS = 6
QUOTA_RETRY_S = 45  # kvota tufayli ulanmagan sessiya shuncha soniyadan keyin qayta urinadi
MAX_LAG_S = 2.0  # tarjima videodan shuncha orqada qolsa — video bir zum pauza, tarjima ovozi yetib oladi
LATE_BUFFER_S = 0.5  # navbatdagi tarjima tayyor emas, video esa shuncha o'tib ketdi — video buferlash uchun pauza
TRANSCRIPT_PREFIX = "[Tarjima] "
EXTRA_BIN_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")
IS_WINDOWS = sys.platform == "win32"
# Windows: oynasiz .exe'dan ffmpeg/yt-dlp chaqirilganda konsol oynasi chiqmasin
NO_WINDOW: dict[str, Any] = {"creationflags": 0x08000000} if IS_WINDOWS else {}
INSTALL_HINT = "winget install yt-dlp.yt-dlp Gyan.FFmpeg" if IS_WINDOWS else "brew install yt-dlp ffmpeg"

LANG_NAMES = {"uz": "Uzbek (Latin script)", "ru": "Russian", "en": "English", "tr": "Turkish", "kk": "Kazakh"}

_YT_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|live/|embed/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)

_STATE_JS = (
    "(function(){var v=document.querySelector('video');if(!v){return 'novideo';}"
    "var ad=!!document.querySelector('.ad-showing,.ad-interrupting');"
    "return JSON.stringify({t:v.currentTime,p:v.paused,r:v.playbackRate,e:v.ended,ad:ad,"
    "d:v.duration||0,href:location.href});})()"
)


# ---------------------------------------------------------------------------
# Toza funksiyalar
# ---------------------------------------------------------------------------
def youtube_id(url: str | None) -> str | None:
    m = _YT_RE.search(url or "")
    return m.group(1) if m else None


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def find_binary(name: str, env_var: str | None = None) -> str | None:
    """PATH + Homebrew papkalari (.app ichidan ishga tushganda PATH qisqa bo'ladi)."""
    override = (os.getenv(env_var) or "").strip() if env_var else ""
    if override and os.path.isfile(override):
        return override
    found = shutil.which(name)
    if found:
        return found
    for d in EXTRA_BIN_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


NO_TAB = "__nexus_no_tab__"


def video_tab_script(browser: str, video_id: str, js: str, tab_id: str | None = None) -> str:
    """AppleScript: JS ni video tabida bajaradi — Chrome'da `tab_id` bo'yicha (bir xil video bir nechta
    tabda ochiq bo'lishi mumkin), aks holda barcha oynalardan URL'ida `video_id` bor birinchi tab."""
    from nexus.browser_actions import js_to_applescript

    code = js_to_applescript(js)
    vid = re.sub(r"[^A-Za-z0-9_-]", "", video_id)
    tid = re.sub(r"\D", "", tab_id or "")
    if browser == "safari":
        app, run = "Safari", f'do JavaScript "{code}" in t'
        match = f'URL of t contains "{vid}"'
    else:
        app, run = "Google Chrome", f'execute t javascript "{code}"'
        match = f'(id of t as text) is "{tid}"' if tid else f'URL of t contains "{vid}"'
    return (
        f'tell application "{app}"\n'
        "  repeat with w in windows\n"
        "    repeat with t in tabs of w\n"
        f"      if {match} then return ({run})\n"
        "    end repeat\n"
        "  end repeat\n"
        f'  return "{NO_TAB}"\n'
        "end tell"
    )


def find_tab_script(video_id: str) -> str:
    """AppleScript (Chrome): `video_id` ochiq tabni topib oldinga chiqaradi va id sini qaytaradi ("" — yo'q)."""
    vid = re.sub(r"[^A-Za-z0-9_-]", "", video_id)
    return (
        'tell application "Google Chrome"\n'
        "  repeat with w in windows\n"
        "    set i to 0\n"
        "    repeat with t in tabs of w\n"
        "      set i to i + 1\n"
        f'      if URL of t contains "{vid}" then\n'
        "        set active tab index of w to i\n"
        "        set index of w to 1\n"
        "        activate\n"
        "        return (id of t) as text\n"
        "      end if\n"
        "    end repeat\n"
        "  end repeat\n"
        '  return ""\n'
        "end tell"
    )


def player_setup_js(volume: float, play: bool) -> str:
    """Pleyer: asl ovozni o'chirish/pasaytirish (0..1, manfiy — tegilmaydi) va ijro yoki pauza."""
    if volume < 0:  # ovozga tegilmaydi (seek'dan keyingi pauza/davom)
        body = ""
    else:
        body = "v.muted=true;" if volume == 0 else f"v.muted=false;v.volume={volume:.3f};"
    body += "var p=v.play();if(p&&p.catch){p.catch(function(){});}" if play else "v.pause();"
    return "(function(){var v=document.querySelector('video');if(!v){return 'novideo';}" + body + "return 'ok';})()"


def build_ytdlp_cmd(ytdlp: str, url: str, out_dir: str) -> list[str]:
    """Faqat audio yuklanadi; stdout: 1-qator sarlavha, oxirgi qator fayl yo'li."""
    return [
        ytdlp, "-q", "--no-warnings", "--no-playlist", "--match-filter", "!is_live",
        "-f", "bestaudio/best", "--no-simulate",
        "--print", "before_dl:%(title)s", "--print", "after_move:filepath",
        "-o", os.path.join(out_dir, "%(id)s.%(ext)s"), url,
    ]


def build_ffmpeg_cmd(ffmpeg: str, stream_url: str, start_s: float) -> list[str]:
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin"]
    if stream_url.startswith("http"):
        cmd += ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5"]
    if start_s > 0.05:
        cmd += ["-ss", f"{start_s:.2f}"]
    cmd += ["-i", stream_url, "-vn", "-ac", "1", "-ar", str(IN_RATE), "-f", "s16le", "pipe:1"]
    return cmd


def translator_instruction(target: str = "uz", source: str = "en") -> str:
    tgt = LANG_NAMES.get(target, target)
    src = LANG_NAMES.get(source, source)
    return (
        f"You are a voice-over dubbing interpreter. Every input turn is the next fragment of the {src} video "
        f"soundtrack. Reply by speaking the {tgt} translation of exactly that fragment, in first person as the "
        f"speaker would say it, and nothing else. Fragments may be cut mid-sentence: translate what is there and "
        f"continue naturally in the next turn; never skip anything. Keep it concise — no longer than the original. "
        f"No labels such as 'Translation:', no brackets, no notes, no descriptions of sounds or pauses. Never answer "
        f"or comment on what is said. Keep names and numbers accurate. If a fragment has no speech (music, "
        f"laughter, noise), stay silent."
    )


_JUNK_RE = re.compile(
    r"[<>{}\[\]]|translation\s*:|no speech|\bpause\b|^\W*\(?\s*(uzbek|o['‘’`]?zbek)\w*\s*\)?\s*:", re.IGNORECASE
)


def is_junk_translation(text: str) -> bool:
    """Model tarjima o'rniga yorliq/izoh aytdi (`(Uzbek translation: …)`, `<no speech>{pause}`)."""
    return bool(_JUNK_RE.search(text or ""))


def parse_player_state(raw: str) -> dict[str, Any] | None:
    raw = (raw or "").strip()
    if not raw or raw == "novideo":
        return None
    try:
        d = json.loads(raw)
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


@dataclass
class PlaybackClock:
    """Brauzer pleyeri holatidan joriy video vaqtini baholaydi (so'rovlar orasida interpolyatsiya)."""

    t: float = 0.0
    ts: float = 0.0  # t o'lchangan monotonic vaqt
    paused: bool = True
    ad: bool = False
    ended: bool = False
    rate: float = 1.0
    duration: float = 0.0
    known: bool = False

    def update(self, state: dict[str, Any], now: float) -> None:
        try:
            self.t = max(0.0, float(state.get("t") or 0.0))
            self.rate = float(state.get("r") or 1.0) or 1.0
            self.duration = max(0.0, float(state.get("d") or 0.0))
        except (TypeError, ValueError):
            return
        self.paused = bool(state.get("p"))
        self.ad = bool(state.get("ad"))
        self.ended = bool(state.get("e"))
        self.ts = now
        self.known = True

    @property
    def halted(self) -> bool:
        return self.paused or self.ad or self.ended or not self.known

    def position(self, now: float) -> float:
        if self.halted:
            return self.t
        return self.t + max(0.0, now - self.ts) * self.rate


class Segmenter:
    """Uzluksiz nutqni tarjima bo'laklariga ajratadi: `push(rms)` True → bo'lakni shu chunk bilan yopish."""

    def __init__(
        self, min_s: float = SEGMENT_MIN_S, max_s: float = SEGMENT_MAX_S, quiet_ratio: float = SEGMENT_QUIET_RATIO
    ) -> None:
        self.min_s, self.max_s, self.quiet_ratio = min_s, max_s, quiet_ratio
        self.reset()

    def reset(self) -> None:
        self.length_s = 0.0
        self._sum = 0.0
        self._n = 0

    def push(self, rms: float, chunk_s: float = CHUNK_S) -> bool:
        self.length_s += chunk_s
        avg = self._sum / self._n if self._n else 0.0
        self._sum += rms
        self._n += 1
        quiet = avg > 0 and rms < self.quiet_ratio * avg
        end = self.length_s >= self.max_s or (self.length_s >= self.min_s and quiet)
        if end:
            self.reset()
        return end


def is_quota_error(exc: BaseException) -> bool:
    """Kalit kvotasi (bir vaqtdagi sessiyalar soni yoki kunlik limit) tugadi."""
    low = str(exc).lower()
    return "exceeded your current quota" in low or "resource_exhausted" in low


def is_silent(seg: Any) -> bool:
    """Bo'lak deyarli jim (o'rtacha RMS `SILENT_RMS` dan past)."""
    n = len(seg.input)
    return n > 0 and seg.rms_sum / n < SILENT_RMS


def fit_tempo(out_s: float, window_s: float) -> float:
    """Tarjima (`out_s`) videodagi qolgan oralig'iga (`window_s`) sig'ishi uchun tezlik (1.0..MAX_TEMPO)."""
    if out_s <= 0:
        return 1.0
    if window_s <= 0.2:
        return MAX_TEMPO
    t = out_s / window_s
    return 1.0 if t < 1.05 else round(min(MAX_TEMPO, t), 2)


async def time_stretch(ffmpeg: str, pcm: bytes, rate: int, tempo: float) -> bytes:
    """s16le mono PCM ni ohangini saqlab `tempo` barobar tezlashtiradi (ffmpeg atempo). Xatoda — o'zgarishsiz."""
    if tempo <= 1.0 or not pcm or not ffmpeg:
        return pcm
    fmt = ["-f", "s16le", "-ar", str(rate), "-ac", "1"]
    try:
        proc = await asyncio.create_subprocess_exec(
            ffmpeg, "-hide_banner", "-loglevel", "error", *fmt, "-i", "pipe:0",
            "-filter:a", f"atempo={tempo:.3f}", *fmt, "pipe:1",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            **NO_WINDOW,
        )
        out, _ = await asyncio.wait_for(proc.communicate(pcm), timeout=5.0)
    except (OSError, TimeoutError) as e:
        log.debug("atempo ishlamadi: %s", e)
        return pcm
    return out or pcm


def feed_action(sent_pos: float, video_pos: float, can_resync: bool, lookahead: float | None = None) -> str:
    """Navbatdagi chunk bilan nima qilish: "resync" | "wait" | "send".

    Audio videodan `lookahead` gacha oldinda yuboriladi (pauzada ham — tarjima tayyor tursin)."""
    lookahead = LOOKAHEAD_S if lookahead is None else lookahead
    if can_resync and (sent_pos < video_pos - RESYNC_S or sent_pos > video_pos + lookahead + RESYNC_S):
        return "resync"
    if sent_pos > video_pos + lookahead:
        return "wait"
    return "send"


@dataclass
class Segment:
    """Tarjima bo'lagi: kiruvchi audio (tayinlanguncha `buf`da) va modelning javobi (`audio`)."""

    seq: int
    started_at: float = 0.0
    src_start: float = 0.0  # videodagi boshlanish (s)
    src_end: float = 0.0
    buf: list[bytes] = field(default_factory=list)
    input: list[bytes] = field(default_factory=list)  # butun kiruvchi audio (qayta urinish uchun)
    retries: int = 0
    rms_sum: float = 0.0
    closed: bool = False  # kiruvchi audio tugadi (activity_end kerak)
    ended_at: float | None = None  # activity_end yuborilgan payt
    audio: deque[bytes] = field(default_factory=deque)
    audio_bytes: int = 0
    first_audio_at: float | None = None
    text: str = ""
    done: bool = False  # boshqa javob kelmaydi (turn_complete / timeout / tashlandi)
    lag: float | None = None  # ijro boshlanganda video bo'lak boshidan qancha o'tgan (s) — sinxron metrikasi
    tempo: float = 1.0
    dropped: bool = False  # ijro etilmaydi (seek, kech qolgan yoki izoh)
    seek_dropped: bool = False  # seek tufayli tashlandi — videodagi bu oraliq "qoplangan" hisoblanmaydi
    worker: Any = None


class _Worker:
    """Bitta Live sessiya: navbatdagi bo'lakni oladi, javobini bo'lakka yozadi."""

    def __init__(self, idx: int) -> None:
        self.idx = idx
        self.inbox: asyncio.Queue[Any] = asyncio.Queue()
        self.seg: Segment | None = None
        self.resume_handle: str | None = None
        self.ended_at: float | None = None  # oxirgi activity_end; turn_complete gacha sessiya band
        self.connected = False
        self.quota_waiting = False


def segment_expired(seg: Segment, now: float, no_response_s: float = NO_RESPONSE_S) -> bool:
    """activity_end dan keyin `no_response_s` ichida audio kelmadi — ijroda o'tkazib yuboriladi."""
    return seg.ended_at is not None and seg.first_audio_at is None and now - seg.ended_at > no_response_s


# ---------------------------------------------------------------------------
# Tarjimon
# ---------------------------------------------------------------------------
class VideoTranslator:
    def __init__(self, bus: Any = None, settings: Any = None, audio: Any = None) -> None:
        self.bus = bus
        self.settings = settings
        self.audio = audio
        self.player: Any = None
        self.clock = PlaybackClock()
        self.browser = "chrome"
        self.video_id = ""
        self.target = "uz"
        self._task: asyncio.Task | None = None
        self._queue: asyncio.Queue[tuple[float, bytes]] = asyncio.Queue()  # (video vaqti, PCM)
        self._ready_until = -1.0  # shu video vaqtigacha tarjima ijroga qo'yilgan (buferlash uchun)
        self._eof = False  # audio fayl oxirigacha yuborildi
        self.junk = 0  # yorliq/izoh aytilgani uchun tashlangan bo'laklar
        self.buffered = 0  # tarjima orqada qolib video pauza qilingan marta
        self.catchups = 0  # tarjima ovozi videoga yetib olishi uchun qilingan qisqa pauzalar
        self._catchup = False
        self._quota_hit = False
        self._tab_id: str | None = None  # Chrome: biz ochgan tab
        self._gate: asyncio.Task | None = None  # seek'dan keyin "buferlash" (video pauzada)
        self._audio_path = ""
        self._tmpdir = ""
        self._ytdlp = ""
        self._ffmpeg = ""
        self._proc: asyncio.subprocess.Process | None = None
        self._mode = "prompt"
        self._free: deque[_Worker] = deque()  # bo'sh sessiyalar
        self._segments: dict[int, Segment] = {}
        self._unassigned: deque[Segment] = deque()
        self._workers: list[_Worker] = []
        self._seq = 0
        self._epoch = 0  # seek'da oshadi — dispetcher ochiq bo'lakni tashlaydi
        self.history: list[Segment] = []  # ijro etilgan bo'laklar (metrika/sinov uchun)
        self.skipped = 0  # javobsiz qolib o'tkazilgan bo'laklar

    # --- holat ---
    @property
    def active(self) -> bool:
        return self._task is not None and not self._task.done()

    def is_playing(self) -> bool:
        p = self.player
        return bool(self.active and p is not None and not p.hold and p.is_playing)

    def _log(self, message: str, level: str = "info") -> None:
        getattr(log, "warning" if level == "warn" else level, log.info)(message)
        if self.bus is not None:
            self.bus.publish("LOG", {"level": level, "message": message})

    def _setting(self, name: str, default: Any) -> Any:
        return getattr(self.settings, name, default) if self.settings is not None else default

    # --- ochiq API ---
    async def start(self, url: str, browser: str, original_volume: float = 0.0, target: str = "uz") -> dict:
        vid = youtube_id(url)
        if not vid:
            return {"ok": False, "output": "", "error": "Bu YouTube video havolasi emas"}
        ytdlp = find_binary("yt-dlp", "YTDLP_PATH")
        ffmpeg = find_binary("ffmpeg", "FFMPEG_PATH")
        if not ytdlp or not ffmpeg:
            missing = ", ".join(n for n, p in (("yt-dlp", ytdlp), ("ffmpeg", ffmpeg)) if not p)
            return {"ok": False, "output": "", "error": f"O'rnatilmagan: {missing} ({INSTALL_HINT})"}
        if self.settings is None:
            from nexus.config import settings

            self.settings = settings
        if not (self._setting("gemini_api_key", "") or "").strip():
            return {"ok": False, "output": "", "error": "GEMINI_API_KEY yo'q"}

        await self.stop()
        self.video_id, self.browser, self.target = vid, browser, target or "uz"
        self._ytdlp, self._ffmpeg = ytdlp, ffmpeg
        self.clock = PlaybackClock()
        self._queue = asyncio.Queue()
        self._ready_until = -1.0
        self._eof = False
        self._tab_id = None
        self._quota_hit = False
        self.skipped = self.junk = self.buffered = self.catchups = 0
        self.history = []
        self._mode = str(self._setting("video_translate_mode", "prompt") or "prompt").lower()
        self._task = asyncio.create_task(self._run(original_volume), name="video-translate")
        return {
            "ok": True,
            "output": "Video ochilmoqda, audio yuklangach o'zbekcha tarjima boshlanadi. "
            "To'xtatish: \"tarjimani to'xtat\".",
        }

    async def stop(self) -> bool:
        task, self._task = self._task, None
        if task is None or task.done():
            return False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:  # noqa: BLE001
            log.debug("Tarjima taski xato bilan tugadi: %s", e)
        return True

    # --- tayyorgarlik ---
    async def _download(self) -> tuple[bool, str]:
        """yt-dlp: audio faylni vaqtinchalik papkaga yuklaydi. (ok, sarlavha | xato).

        YouTube vaqti-vaqti bilan 403 qaytaradi — bir necha marta urinib ko'riladi."""
        self._tmpdir = self._tmpdir or tempfile.mkdtemp(prefix="nexus-vt-")
        result: tuple[bool, str] = (False, "Video audiosi olinmadi")
        for attempt in range(DOWNLOAD_ATTEMPTS):
            if attempt:
                await asyncio.sleep(1.0 * attempt)
            result = await self._download_once()
            if result[0]:
                break
            log.info("yt-dlp urinish %d: %s", attempt + 1, result[1])
        return result

    async def _download_once(self) -> tuple[bool, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *build_ytdlp_cmd(self._ytdlp, watch_url(self.video_id), self._tmpdir),
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, **NO_WINDOW,
            )
        except OSError as e:
            return False, f"yt-dlp ishga tushmadi: {e}"
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=DOWNLOAD_TIMEOUT_S)
        except TimeoutError:
            return False, "Video audiosi yuklanmadi (vaqt tugadi)"
        finally:
            if proc.returncode is None:
                proc.kill()
        lines = [x.strip() for x in out.decode(errors="replace").splitlines() if x.strip()]
        path = lines[-1] if lines else ""
        if proc.returncode != 0 or not os.path.isfile(path):
            msg = err.decode(errors="replace").strip().splitlines()
            reason = msg[-1] if msg else "jonli efir yoki noma'lum xato"
            return False, f"Video audiosi olinmadi: {reason}"
        self._audio_path = path
        return True, lines[0] if len(lines) > 1 else self.video_id

    async def _js(self, js: str) -> tuple[bool, str]:
        """JS ni video ochilgan tabda bajaradi (faol tab emas — foydalanuvchi boshqa tabga o'tishi mumkin)."""
        if IS_WINDOWS:  # video Nexus'ning WebView2 oynasida
            from nexus.windows_video import host

            return await host.eval(js)
        from nexus.browser_actions import BROWSERS
        from nexus.macos_actions import run_applescript

        if self.browser not in BROWSERS:
            return False, f"Noma'lum brauzer: {self.browser}"
        ok, out = await run_applescript(video_tab_script(self.browser, self.video_id, js, self._tab_id))
        if not ok:
            return False, out
        return (False, "Video tabi topilmadi") if out.strip() == NO_TAB else (True, out)

    async def _open_video(self) -> bool:
        if IS_WINDOWS:
            from nexus.windows_video import host

            ok, out = await host.open(watch_url(self.video_id))
            if not ok:
                self._log(out, "warn")
                return False
            return await self._setup_player()
        from nexus.browser_actions import BrowserController
        from nexus.macos_actions import run_applescript

        if self.browser == "chrome":  # video allaqachon ochiq bo'lsa — yangi tab ochmaymiz
            ok, out = await run_applescript(find_tab_script(self.video_id))
            if ok and out.strip().isdigit():
                self._tab_id = out.strip()
        ok, out = (True, "") if self._tab_id else await BrowserController().open_url(
            self.browser, watch_url(self.video_id)
        )
        if not ok:
            self._log(out, "warn")
            return False
        if self.browser == "chrome" and not self._tab_id:  # yangi tab faol — id sini eslab qolamiz
            ok, out = await run_applescript(
                'tell application "Google Chrome" to return (id of active tab of front window) as text'
            )
            self._tab_id = out.strip() if ok and out.strip().isdigit() else None
        return await self._setup_player()

    async def _setup_player(self) -> bool:
        setup = player_setup_js(0.0, play=False)  # audio yuklanguncha jim pauza
        deadline = time.monotonic() + VIDEO_WAIT_S
        while time.monotonic() < deadline:
            await asyncio.sleep(1.0)
            ok, out = await self._js(setup)
            if ok and out.strip() == "ok":
                return True
        hint = "" if IS_WINDOWS else " (Chrome: View → Developer → Allow JavaScript from Apple Events)"
        self._log(f"Video pleyer topilmadi{hint}", "warn")
        return False

    # --- asosiy sikl ---
    async def _run(self, original_volume: float) -> None:
        from nexus.audio_streamer import AudioPlayer

        s = self.settings
        self.player = AudioPlayer(
            sample_rate=int(getattr(s, "output_sample_rate", 24000)),
            enabled=bool(getattr(s, "playback_enabled", True)),
            bus=self.bus,
            prebuffer_ms=int(getattr(s, "playback_prebuffer_ms", 220)),
            latency=getattr(s, "playback_latency", "high"),
        )
        self.player.start()
        tasks: list[asyncio.Task] = []
        try:
            download = asyncio.create_task(self._download(), name="vt-download")
            opened = await self._open_video()
            ok, info = await download
            if not ok:
                self._log(info, "warn")
                return
            if not opened:
                return
            tasks = [
                asyncio.create_task(self._poll(), name="vt-poll"),
                asyncio.create_task(self._feed(), name="vt-feed"),
                asyncio.create_task(self._translate(), name="vt-translate"),
            ]
            # Video oldinda tarjima tayyor bo'lguncha pauzada — keyin tarjima video bilan birga boradi
            vol = max(0.0, min(100.0, float(original_volume or 0.0))) / 100
            await self._buffer(force=True, volume=vol)
            self._log(f"Video tarjimasi boshlandi: {info}")
            pending = set(tasks)
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                failed = [t for t in done if not t.cancelled() and t.exception() is not None]
                for t in failed:
                    self._log(f"Video tarjimasi xatosi: {t.exception()}", "warn")
                # Audio fayl tugashi (feed) — video/tarjima davom etadi; poll yoki sessiya tugasa — to'xtaymiz
                if failed or any(t is not tasks[1] for t in done):
                    break
            # Video tugadi — oxirgi tarjimani eshittirib bo'lamiz
            if self.clock.ended:
                await asyncio.sleep(1.5)
                self.player.play_out()
                for _ in range(200):
                    if not self.player.is_playing:
                        break
                    await asyncio.sleep(0.1)
        finally:
            if self._gate is not None:
                tasks.append(self._gate)
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await self._kill_ffmpeg()
            self.player.stop()
            if self._tmpdir:
                shutil.rmtree(self._tmpdir, ignore_errors=True)
                self._tmpdir = ""
            self._log("Video tarjimasi to'xtadi")

    async def _poll(self) -> None:
        """Pleyer holatini kuzatadi; tab boshqa sahifaga o'tsa yoki video tugasa — tugaydi."""
        misses = 0
        while True:
            ok, out = await self._js(_STATE_JS)
            state = parse_player_state(out) if ok else None
            if state is None or self.video_id not in str(state.get("href", "")):
                misses += 1
                if misses >= 6:  # ~3 s video topilmadi / boshqa sahifa
                    self._log("Video sahifasi yopildi — tarjima to'xtatildi")
                    return
            else:
                misses = 0
                self.clock.update(state, time.monotonic())
                if self.player is not None:
                    # pauza — tarjima ovozi ham to'xtab turadi (yetib olish pauzasidan tashqari)
                    self.player.hold = self.clock.paused and not self.clock.ended and not self._catchup
                if self.clock.ended:
                    return
            await asyncio.sleep(POLL_S)

    async def _spawn_ffmpeg(self, start_s: float) -> asyncio.subprocess.Process:
        await self._kill_ffmpeg()
        self._eof = False
        self._proc = await asyncio.create_subprocess_exec(
            *build_ffmpeg_cmd(self._ffmpeg, self._audio_path, start_s),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, **NO_WINDOW,
        )
        return self._proc

    async def _kill_ffmpeg(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.returncode is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            # stdout quvuri to'la bo'lsa wait() EOF ni kutib osilib qoladi — qoldiqni o'qib tashlaymiz
            try:
                await asyncio.wait_for(proc.communicate(), timeout=3.0)
            except (TimeoutError, OSError) as e:
                log.debug("ffmpeg yopilmadi: %s", e)

    def _drop_pending(self) -> None:
        """Seek: navbatdagi kiruvchi audio va hali ijro etilmagan tarjimalar tashlanadi."""
        while not self._queue.empty():
            self._queue.get_nowait()
        self._epoch += 1
        self._ready_until = -1.0
        for seg in self._segments.values():
            seg.dropped = seg.done = seg.seek_dropped = True
            seg.audio.clear()
        self._unassigned.clear()
        if self.player is not None:
            self.player.clear()

    async def _feed(self) -> None:
        """ffmpeg PCM → navbat (video vaqti bilan), videodan `LOOKAHEAD_S` oldinda; seek → qayta boshlash."""
        while not self.clock.known:
            await asyncio.sleep(0.1)
        pos = self.clock.position(time.monotonic())
        proc = await self._spawn_ffmpeg(pos)
        spawned = time.monotonic()
        while True:
            now = time.monotonic()
            video = self.clock.position(now)
            action = feed_action(pos, video, now - spawned > RESYNC_GRACE_S)
            if action == "resync":
                log.info("Resync: audio %.1fs, video %.1fs", pos, video)
                self._drop_pending()
                self._start_gate()
                pos = video
                proc = await self._spawn_ffmpeg(pos)
                spawned = time.monotonic()
                continue
            if action == "wait":
                await asyncio.sleep(0.05)
                continue
            assert proc.stdout is not None
            try:
                chunk = await proc.stdout.readexactly(CHUNK_BYTES)
            except asyncio.IncompleteReadError:
                self._eof = True
                # Fayl tugadi. Foydalanuvchi orqaga o'tkazsa — resync qayta boshlaydi
                while feed_action(pos, self.clock.position(time.monotonic()), True) != "resync":
                    await asyncio.sleep(0.2)
                continue
            self._queue.put_nowait((pos, chunk))
            pos += CHUNK_S

    # --- Gemini sessiyasi ---
    def _build_config(self, native: bool, resume_handle: str | None = None) -> Any:
        from google.genai import types

        s = self.settings
        kwargs: dict[str, Any] = {}
        if native:
            kwargs["translation_config"] = types.TranslationConfig(
                target_language_code=self.target, echo_target_language=False
            )
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=translator_instruction(self.target),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=getattr(s, "gemini_voice", "Aoede"))
                )
            ),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(disabled=True),
                activity_handling=types.ActivityHandling.NO_INTERRUPTION,
            ),
            session_resumption=types.SessionResumptionConfig(handle=resume_handle),
            context_window_compression=types.ContextWindowCompressionConfig(sliding_window=types.SlidingWindow()),
            **kwargs,
        )

    async def _translate(self) -> None:
        """Parallel sessiyalar + dispetcher + tartibli ijro."""
        n = max(1, int(self._setting("video_translate_sessions", DEFAULT_SESSIONS) or DEFAULT_SESSIONS))
        self._free = deque()
        self._segments, self._unassigned, self._seq = {}, deque(), 0
        client = self.settings.make_client()
        self._workers = [_Worker(i) for i in range(n)]
        workers = [asyncio.create_task(self._worker(w, client), name=f"vt-worker{w.idx}") for w in self._workers]
        main = [
            asyncio.create_task(self._dispatch(), name="vt-dispatch"),
            asyncio.create_task(self._playout(), name="vt-playout"),
        ]
        tasks = workers + main
        try:
            pending = set(tasks)
            while True:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for t in done:
                    if not t.cancelled() and t.exception() is not None:
                        raise t.exception()
                if any(t in done for t in main):
                    return
                # Bitta sessiya ulanmay qolsa qolganlari ishlayveradi; hammasi o'chsa — tarjima to'xtaydi
                if all(t.done() for t in workers):
                    if self._quota_hit:
                        raise RuntimeError("Gemini API kvotasi tugadi (Live sessiyalar ochilmadi) — keyinroq urining")
                    raise RuntimeError("Tarjimon sessiyalari ulanmadi")
        finally:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    # --- dispetcher: navbat → bo'laklar → bo'sh sessiyalar ---
    def _pump(self) -> None:
        """Tayinlanmagan bo'laklarni (FIFO) bo'sh sessiyalarga beradi."""
        while self._unassigned and self._free:
            seg = self._unassigned[0]
            if seg.dropped or seg.done:
                self._unassigned.popleft()
                continue
            if not seg.closed:  # bo'lak hali yig'ilyapti — to'liq bo'lgach bir zumda yuboriladi
                break
            self._unassigned.popleft()
            w = self._free.popleft()
            w.seg, seg.worker = seg, w
            w.inbox.put_nowait(("start", seg))
            for chunk in seg.buf:
                w.inbox.put_nowait(chunk)
            seg.buf.clear()
            if seg.closed:
                w.inbox.put_nowait(("end", seg))

    def _close(self, seg: Segment) -> None:
        seg.closed = True
        if is_silent(seg):  # jimlik — API'ga yuborilmaydi, ijroda jimgina o'tkaziladi
            seg.done = True
            seg.buf.clear()
        self._pump()

    async def _dispatch(self) -> None:
        from nexus.audio_streamer import compute_rms

        seg: Segment | None = None
        segmenter = Segmenter()
        epoch = self._epoch
        while True:
            try:
                pos, chunk = await asyncio.wait_for(self._queue.get(), timeout=IDLE_END_S)
            except TimeoutError:
                if seg is not None:  # pauza — boshlangan gapni tarjimaga topshiramiz
                    self._close(seg)
                    seg = None
                    segmenter.reset()
                self._pump()
                continue
            if epoch != self._epoch:  # seek — ochiq bo'lak allaqachon tashlangan
                epoch, seg = self._epoch, None
                segmenter.reset()
            if seg is None:
                seg = Segment(seq=self._seq, started_at=time.monotonic(), src_start=pos)
                self._seq += 1
                self._segments[seg.seq] = seg
                self._unassigned.append(seg)
            seg.src_end = pos + CHUNK_S
            seg.input.append(chunk)
            seg.buf.append(chunk)
            rms = compute_rms(chunk)[0]
            seg.rms_sum += rms
            if segmenter.push(rms):
                self._close(seg)
                seg = None
            self._pump()

    # --- sessiya ---
    async def _worker(self, w: _Worker, client: Any) -> None:
        from nexus.gemini_live_client import compute_backoff

        model = str(self._setting("video_translate_model", "") or self.settings.gemini_model)
        fails = 0
        while True:
            started = time.monotonic()
            try:
                config = self._build_config(self._mode == "native")
                async with client.aio.live.connect(model=model, config=config) as session:
                    log.info("Tarjimon sessiyasi #%d ulandi (%s)", w.idx, model)
                    started = time.monotonic()
                    w.connected = True
                    if w.quota_waiting:
                        log.info("Sessiya #%d kvota bo'shagach ulandi", w.idx)
                    w.quota_waiting = False
                    self._release(w)
                    pair = [
                        asyncio.create_task(self._worker_send(w, session), name=f"vt-send{w.idx}"),
                        asyncio.create_task(self._worker_recv(w, session), name=f"vt-recv{w.idx}"),
                    ]
                    try:
                        done, _ = await asyncio.wait(pair, return_when=asyncio.FIRST_COMPLETED)
                    finally:
                        for t in pair:
                            t.cancel()
                        await asyncio.gather(*pair, return_exceptions=True)
                    for t in done:
                        if not t.cancelled() and t.exception() is not None:
                            raise t.exception()
                fails = 0 if time.monotonic() - started > 30 else fails
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001 — sessiya xatosi: qayta ulanamiz yoki shu sessiyani o'chiramiz
                fails += 1
                if is_quota_error(e):
                    self._quota_hit = True
                    alive = sum(1 for x in self._workers if x.connected and x is not w)
                    if alive:  # kvota bir vaqtdagi sessiyalar soniga yetdi — qolganlari ishlaydi, bu keyinroq uriniladi
                        if not w.quota_waiting:
                            log.info("Sessiya #%d: kvota — %ds dan keyin qayta uriniladi", w.idx, QUOTA_RETRY_S)
                        w.quota_waiting = True
                        fails -= 1  # kvota kutish "ulanmadi" hisoblanmaydi
                        self._detach(w)
                        await asyncio.sleep(QUOTA_RETRY_S)
                        continue
                    self._log("Gemini API kvotasi yetmadi — qayta urinilmoqda", "warn")
                else:
                    self._log(f"Tarjimon sessiyasi #{w.idx} uzildi: {type(e).__name__}: {e}", "warn")
                if fails >= MAX_SESSION_FAILS:
                    log.warning("Tarjimon sessiyasi #%d o'chirildi (%d marta ulanmadi)", w.idx, fails)
                    return
                await asyncio.sleep(compute_backoff(fails - 1, 1.0, 15.0))
            finally:
                self._detach(w)
            await asyncio.sleep(0.05)

    def _release(self, w: _Worker) -> None:
        """Sessiya bo'shadi — navbatdagi bo'lakni olishi mumkin."""
        w.seg = None
        w.ended_at = None
        while not w.inbox.empty():
            w.inbox.get_nowait()
        if w.connected and w not in self._free:
            self._free.append(w)
        self._pump()

    def _detach(self, w: _Worker) -> None:
        """Sessiya uzildi: joriy bo'lak yakunlangan deb belgilanadi, o'zi bo'sh ro'yxatdan chiqariladi."""
        w.connected = False
        w.ended_at = None
        if w.seg is not None:
            w.seg.done = True
            w.seg = None
        if w in self._free:
            self._free.remove(w)

    async def _worker_send(self, w: _Worker, session: Any) -> None:
        from google.genai import types

        mime = f"audio/pcm;rate={IN_RATE}"
        while True:
            item = await w.inbox.get()
            if isinstance(item, tuple):
                kind, seg = item
                if kind == "start":
                    await session.send_realtime_input(activity_start=types.ActivityStart())
                else:
                    await session.send_realtime_input(activity_end=types.ActivityEnd())
                    seg.ended_at = w.ended_at = time.monotonic()
                continue
            await session.send_realtime_input(audio=types.Blob(data=item, mime_type=mime))

    async def _worker_recv(self, w: _Worker, session: Any) -> None:
        while True:
            received = False
            async for msg in session.receive():
                received = True
                sru = getattr(msg, "session_resumption_update", None)
                if sru is not None and getattr(sru, "resumable", False) and getattr(sru, "new_handle", None):
                    w.resume_handle = sru.new_handle
                sc = getattr(msg, "server_content", None)
                if sc is not None and self._on_content(w, sc):
                    return  # bo'lak tayyor — sessiya yopiladi, worker yangisini ochadi
                if getattr(msg, "go_away", None) is not None:
                    return
            if not received:
                return

    def _on_content(self, w: _Worker, sc: Any) -> bool:
        """Model javobini sessiyaning joriy bo'lagiga yozadi. True — navbat tugadi (sessiya bo'sh)."""
        seg = w.seg
        live = seg is not None and not seg.dropped
        mt = getattr(sc, "model_turn", None)
        for part in (getattr(mt, "parts", None) or []) if mt is not None else []:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None) if inline is not None else None
            if data and live:
                if seg.first_audio_at is None:
                    seg.first_audio_at = time.monotonic()
                seg.audio.append(data)
                seg.audio_bytes += len(data)
        ot = getattr(sc, "output_transcription", None)
        if ot is not None and getattr(ot, "text", None) and live:
            seg.text += ot.text
        finished = bool(getattr(sc, "generation_complete", None) or getattr(sc, "turn_complete", None))
        if finished and seg is not None:
            if live and is_junk_translation(seg.text) and seg.retries < MAX_RETRIES:
                log.info("Bo'lak #%d: tarjima o'rniga izoh (%s) — qayta yuborildi", seg.seq, seg.text.strip()[:60])
                self._retry(seg)
            else:
                seg.done = True  # audio to'liq keldi (u generation_complete gacha to'liq keladi)
        return finished

    # --- tartibli ijro ---
    def _backlog_s(self) -> float:
        rate = int(getattr(self.player, "sample_rate", 24000) or 24000)
        return self.player.pending_bytes() / (2 * rate)

    async def _playout(self) -> None:
        """Bo'laklarni `seq` tartibida, video o'z oralig'iga (`src_start`) yetganda ijroga qo'yadi.

        Ijro boshlanadigan payt = hozir + pleyer navbati. O'sha paytdagi video vaqti bo'lak boshidan oldin
        bo'lsa — kutamiz. Vaqti kelganda: javob to'liq kelgan bo'lsa — qolgan oraliqqa sig'dirib
        tezlashtiriladi; hali kelayotgan bo'lsa (server audioni ~real vaqtda oqizadi) — kelgan sari
        oddiy tezlikda oqiziladi (to'liq kelishini kutish bo'lak uzunligicha kechikish qo'shardi)."""
        seq = 0
        rate = int(getattr(self.player, "sample_rate", 24000) or 24000)
        streaming: Segment | None = None
        while True:
            now = time.monotonic()
            self._release_stuck(now)
            if streaming is not None:
                seg = streaming
                while seg.audio:
                    self.player.enqueue(seg.audio.popleft())
                if seg.done or seg.dropped:
                    self._played(seg)
                    streaming = None
                    seq += 1
                    continue
                await asyncio.sleep(0.03)
                continue
            seg = self._segments.get(seq)
            if seg is None:
                if self._segments and min(self._segments) > seq:  # seek'dan keyin raqamlar oldinda
                    seq = min(self._segments)
                await asyncio.sleep(0.03)
                continue
            if not seg.dropped and not seg.done and segment_expired(seg, now) and seg.retries < MAX_RETRIES:
                self._retry(seg)
            expired = not seg.done and segment_expired(seg, now)
            if seg.dropped or expired or (seg.done and not seg.audio_bytes):
                if expired:
                    self.skipped += 1
                    log.info("Bo'lak #%d qayta urinishdan keyin ham javobsiz — o'tkazildi", seg.seq)
                self._finish(seg)
                seq += 1
                continue
            if not seg.audio_bytes:  # javob hali boshlanmadi
                self._maybe_buffer(seg, now)
                await asyncio.sleep(0.03)
                continue
            start_v = self.clock.position(now) + self._backlog_s()  # ijro boshlanganda video qayerda bo'ladi
            if start_v < seg.src_start - 0.1:
                await asyncio.sleep(0.03)  # video hali bu joyga yetmadi (yoki pauza)
                continue
            if start_v - seg.src_end > MAX_LATE_S or is_junk_translation(seg.text):
                if is_junk_translation(seg.text):
                    self.junk += 1
                    log.info("Bo'lak #%d tashlandi (tarjima o'rniga izoh): %s", seg.seq, seg.text.strip()[:80])
                else:
                    self.skipped += 1
                    log.info("Bo'lak #%d juda kech qoldi (%.1fs) — o'tkazildi", seg.seq, start_v - seg.src_end)
                seg.dropped = True  # kech kelgan audio ham tashlansin
                self._finish(seg)
                seq += 1
                continue
            seg.lag = max(0.0, start_v - seg.src_start)
            self._ready_until = max(self._ready_until, seg.src_end)
            if seg.lag > MAX_LAG_S:
                self._start_catchup(seg.lag - 0.3)
            if not seg.done:  # javob hali kelyapti — oqim bilan, oddiy tezlikda
                streaming = seg
                continue
            pcm = b"".join(seg.audio)
            seg.audio.clear()
            window = seg.src_end - max(start_v, seg.src_start) + SPILL_S
            seg.tempo = fit_tempo(len(pcm) / (2 * rate), window)
            self.player.enqueue(await time_stretch(self._ffmpeg, pcm, rate, seg.tempo))
            self._played(seg)
            seq += 1

    def _played(self, seg: Segment) -> None:
        self.player.play_out()
        if not seg.dropped:
            self._publish_text(seg)
            self.history.append(seg)
        self._finish(seg)

    def _retry(self, seg: Segment) -> None:
        """Javob bermagan bo'lakni navbat boshiga qaytaradi — boshqa (bo'sh) sessiya oladi."""
        seg.retries += 1
        old = seg.worker
        if old is not None and old.seg is seg:
            old.seg = None  # kech kelgan javob tashlanadi; sessiya turn_complete / timeout da bo'shaydi
        seg.worker, seg.ended_at, seg.first_audio_at = None, None, None
        seg.audio.clear()
        seg.audio_bytes, seg.text, seg.done = 0, "", False
        seg.buf = list(seg.input)
        seg.closed = True
        self._unassigned.appendleft(seg)
        log.info("Bo'lak #%d javobsiz — qayta yuborildi", seg.seq)
        self._pump()

    def _finish(self, seg: Segment) -> None:
        self._segments.pop(seg.seq, None)
        if not seg.seek_dropped:  # jim/izoh/o'tkazilgan bo'lak ham videodagi oraliqni "qoplaydi"
            self._ready_until = max(self._ready_until, seg.src_end)

    def _ready(self, pos: float, ahead: float = GATE_AHEAD_S) -> bool:
        """`pos` dan `ahead` soniya oldinga tarjima tayyormi: ijroga qo'yilgan, yoki bo'laklar javobi keldi
        (yoki o'sha oraliqda bo'lak yo'q — jimlik), yoki audio tugadi."""
        limit = pos + ahead
        if self._ready_until >= limit or (self._eof and not self._segments):
            return True
        covered = max(self._ready_until, pos)
        for seg in sorted(self._segments.values(), key=lambda x: x.seq):
            if seg.seek_dropped:
                continue
            if seg.src_start >= limit:
                return True
            if not (seg.done or seg.audio_bytes >= 48000):  # javob (yoki 1 s audio) hali yo'q
                return False
            covered = max(covered, seg.src_end)
        return covered >= limit or self._eof

    def _start_catchup(self, seconds: float) -> None:
        if (self._gate is not None and not self._gate.done()) or self.clock.halted:
            return
        self.catchups += 1
        log.info("Tarjima %.1fs orqada — video bir zum pauza", seconds + 0.3)
        self._gate = asyncio.create_task(self._catch_up(seconds), name="vt-catchup")

    async def _catch_up(self, seconds: float) -> None:
        """Video pauza, tarjima ovozi esa davom etadi — `seconds` dan keyin video qayta boshlanadi."""
        self._catchup = True
        try:
            await self._js(player_setup_js(-1, play=False))
            self.clock.paused = True
            if self.player is not None:
                self.player.hold = False
            await asyncio.sleep(min(seconds, 8.0))
            await self._js(player_setup_js(-1, play=True))
        finally:
            self._catchup = False

    def _maybe_buffer(self, seg: Segment, now: float) -> None:
        """Tarjima ulgurmayapti (masalan, kvota kam — sessiyalar yetmaydi): gapni tashlab yubormaslik uchun
        video tarjima yetib olguncha pauza qilinadi (YouTube buferlashi kabi)."""
        gate_busy = self._gate is not None and not self._gate.done()
        if gate_busy or self.clock.halted or self._backlog_s() > 0.2:
            return
        if self.clock.position(now) > seg.src_start + LATE_BUFFER_S:
            log.info("Tarjima orqada (bo'lak #%d) — video buferlash uchun pauza", seg.seq)
            self.buffered += 1
            self._start_gate()

    def _start_gate(self) -> None:
        if self._gate is not None and not self._gate.done():
            self._gate.cancel()
        self._gate = asyncio.create_task(self._buffer(force=False), name="vt-buffer")

    async def _buffer(self, force: bool, volume: float = -1) -> None:
        """Buferlash: video pauzada turadi, oldinda `GATE_AHEAD_S` tarjima tayyor bo'lgach davom etadi.

        Boshida (`force`) va seek'dan keyin chaqiriladi; seek paytida foydalanuvchi o'zi pauzada bo'lsa —
        tegilmaydi. YouTube autoplay pauzani bekor qilishi mumkin — shuning uchun qayta-qayta tekshiriladi."""
        while not self.clock.known:
            await asyncio.sleep(0.1)
        if not force and self.clock.paused:
            return
        pos = self.clock.position(time.monotonic())
        deadline = time.monotonic() + FIRST_READY_TIMEOUT_S
        next_pause = 0.0
        while not self._ready(pos) and time.monotonic() < deadline:
            now = time.monotonic()
            if not self.clock.paused and now >= next_pause:
                await self._js(player_setup_js(volume if force else -1, play=False))
                self.clock.paused = True  # keyingi so'rovgacha soat ham to'xtasin
                next_pause = now + 0.5
            await asyncio.sleep(0.1)
        if not self._ready(pos):
            log.info("Buferlash %.0fs da tugamadi — video baribir davom etadi", FIRST_READY_TIMEOUT_S)
        await self._js(player_setup_js(volume, play=True))

    def _release_stuck(self, now: float) -> None:
        """turn_complete kelmay qolgan sessiyani bo'shatadi (model jim qoldi)."""
        for w in self._workers:
            if w.ended_at is not None and now - w.ended_at > WORKER_RELEASE_S and w not in self._free:
                if w.seg is not None:
                    w.seg.done = True
                self._release(w)

    def _publish_text(self, seg: Segment) -> None:
        if seg.text.strip() and self.bus is not None:
            text = TRANSCRIPT_PREFIX + seg.text.strip()
            self.bus.publish("TRANSCRIPT", {"role": "assistant", "text": text, "final": True})


# ---------------------------------------------------------------------------
# Daemon bilan bog'lash va toollar
# ---------------------------------------------------------------------------
translator = VideoTranslator()


def attach(bus: Any, settings: Any, audio: Any = None) -> VideoTranslator:
    """main.py: bus/settings/mikrofonni ulaydi; echo guard tarjima ijrosini ham hisobga oladi."""
    translator.bus, translator.settings, translator.audio = bus, settings, audio
    if audio is not None and hasattr(audio, "extra_playing"):
        audio.extra_playing = translator.is_playing
    return translator


async def shutdown() -> None:
    await translator.stop()


TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "translate_video",
        "description": (
            "Open a YouTube video in the browser with its original sound muted and live-interpret its speech "
            "into Uzbek voice (simultaneous translation, follows pause/seek). Use when the user gives a YouTube "
            "link and asks to translate it / play it in Uzbek."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {"type": "STRING", "description": "YouTube video URL (youtube.com/watch, youtu.be, shorts)."},
                "browser": {"type": "STRING", "description": "chrome or safari (default: chrome)."},
                "original_volume": {
                    "type": "INTEGER",
                    "description": "Original video volume 0-100 under the translation (default 0 = muted).",
                },
                "target_language": {"type": "STRING", "description": "Target language code (default 'uz')."},
            },
            "required": ["url"],
        },
    },
    {
        "name": "stop_video_translation",
        "description": "Stop the running live video translation.",
        "parameters": {"type": "OBJECT", "properties": {}},
    },
]


async def translate_video(args: dict[str, Any]) -> dict[str, Any]:
    from nexus.browser_actions import normalize_browser

    browser = normalize_browser(args.get("browser")) or normalize_browser(os.getenv("DEFAULT_BROWSER")) or "chrome"
    try:
        vol = float(args.get("original_volume") or 0)
    except (TypeError, ValueError):
        vol = 0.0
    target = str(args.get("target_language") or "uz").strip().lower()[:5] or "uz"
    return await translator.start(str(args.get("url") or ""), browser, vol, target)


async def stop_video_translation(_args: dict[str, Any]) -> dict[str, Any]:
    stopped = await translator.stop()
    return {"ok": True, "output": "Tarjima to'xtatildi" if stopped else "Faol tarjima yo'q"}


HANDLERS: dict[str, Any] = {
    "translate_video": translate_video,
    "stop_video_translation": stop_video_translation,
}

__all__ = [
    "HANDLERS",
    "TOOL_DECLARATIONS",
    "PlaybackClock",
    "VideoTranslator",
    "attach",
    "build_ffmpeg_cmd",
    "feed_action",
    "parse_player_state",
    "shutdown",
    "translator",
    "translator_instruction",
    "youtube_id",
]
