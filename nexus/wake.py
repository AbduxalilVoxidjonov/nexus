"""Ism bilan chaqirish (wake): gap yordamchiga qaratilganmi?

Xonada boshqa odamlar bo'lsa, har bir gap mikrofonga tushadi. "Telegramni och"
kompyuterga aytilganmi yoki hamkasbga — buni faqat ism orqali ajratish mumkin.

Nutq tanish ismni buzadi ("Nexus" → "neksus", "нексус"), shuning uchun
solishtirish ataylab yumshoq: tinish belgilari va apostroflar olib tashlanadi,
har bir so'z (va qo'shni juftliklar) ism bilan Levenshtein masofasi orqali
solishtiriladi.

Rejimlar:
    always — har qanday gapga javob beradi (ism talab qilinmaydi)
    name   — faqat ism aytilganda yoki follow-up oynasi ochiq bo'lsa
    smart  — ism, follow-up oynasi, yoki buyruqqa o'xshash qisqa gap

Standart rejim — `name`: xonada boshqa odamlar gapirsa ham yordamchi faqat ismi
bilan chaqirilgan buyruqqa javob beradi. Ism aytilgach `follow_up_s` (8 s) oyna
ochiladi — "ha"/"yo'q" kabi qisqa javobga ism shart emas.

Suhbat rejimi ("kel gaplashamiz"): har gapdan oldin ism aytish shart emas — oxirgi
gapdan keyin `conversation_idle_s` (45 s) davomida hamma gap yordamchiga qaratilgan
hisoblanadi; jimlik yoki "bo'ldi, rahmat" / "suhbatni tugat" rejimni tugatadi.
Bu vaqtda xonadagi boshqa ovozlarga ham javob berilishi mumkin — shuning uchun
rejim faqat aniq iboralar bilan yoqiladi. `touch()` oynani yangilaydi (muvaffaqiyatli
navbat / tool bajarilganda).
"""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, field
from itertools import pairwise

ALWAYS = "always"
NAME = "name"
SMART = "smart"
MODES = (ALWAYS, NAME, SMART)

DEFAULT_CONVERSATION_IDLE_S = 45.0
DEFAULT_FOLLOW_UP_S = 8.0  # qisqa: oynada ismsiz har qanday ovozga (boshqa odamlarnikiga ham) javob beriladi

_PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
_APOSTROPHES = ("'", "`", "ʻ", "ʼ", "’", "‘")

# Kirill → lotin (o'zbek/rus nutq tanish natijalari uchun). Ism odatda lotinda
# beriladi; transkript kirillda kelsa ham mos tushishi uchun.
_CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o", "қ": "q", "ғ": "g", "ҳ": "h",
}

# SMART rejimi uchun: buyruqqa o'xshash so'zlar (qisqa gapda uchrasa — yordamchiga qaratilgan deb hisoblanadi)
_COMMAND_HINTS = (
    "och", "ochib", "yop", "yopib", "ishga tushir", "ovoz", "ovozni", "yoq", "o'chir", "ochir",
    "ekran", "skrinshot", "qidir", "toping", "top", "ayt", "yoz", "ko'rsat", "korsat", "pasaytir",
    "ko'tar", "kotar", "balandlat", "to'xtat", "toxtat", "davom", "keyingi", "oldingi", "qo'y", "qoy",
    "open", "close", "play", "pause", "stop", "search", "type", "show", "volume", "mute", "launch",
    "открой", "закрой", "включи", "выключи", "громкость", "найди", "покажи", "напиши", "запусти",
)
_SMART_MAX_WORDS = 9

# Suhbat rejimini yoqadigan iboralar (normallashtirilgan). "ertaga gaplashamiz" kabi xayrlashuv
# iboralari ataylab yo'q — xonadagi suhbat tasodifan rejimni yoqmasin.
_CONVERSATION_START = (
    "kel gaplashamiz", "keling gaplashamiz", "kel gaplashaylik", "keling gaplashaylik", "qani gaplashaylik",
    "kel suhbatlashamiz", "keling suhbatlashamiz", "kel suhbatlashaylik", "keling suhbatlashaylik",
    "suhbatlashaylik", "suhbat qilaylik", "suhbat qilamiz", "suhbat rejimi", "suhbat rejimini yoq",
    "gaplashib otiraylik", "gaplashib otiramiz",
    "davai pogovorim", "davaite pogovorim", "davai poboltaem",  # давай/давайте (й → i)
    "lets talk", "let s talk", "lets chat", "let s chat",
)
# Suhbat rejimini tugatadigan iboralar
_CONVERSATION_STOP = (
    "suhbatni tugat", "suhbatni toxtat", "suhbatni yakunla", "suhbat tugadi", "suhbat yetarli",
    "boldi rahmat", "rahmat boldi", "boldi yetarli", "xayr", "hayr",
    "xvatit", "poka", "stop talking", "that s all", "thats all", "bye",
)


def normalise(text: str) -> str:
    """Kichik harf, urg'u/apostrofsiz, tinish belgisiz; kirill → lotin."""
    folded = unicodedata.normalize("NFKD", (text or "").lower())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    for a in _APOSTROPHES:
        folded = folded.replace(a, "")
    folded = "".join(_CYR.get(c, c) for c in folded)
    return _PUNCTUATION.sub(" ", folded)


def _has_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    padded = " " + " ".join(normalise(text).split()) + " "
    return any(f" {p} " in padded for p in phrases)


def wants_conversation(text: str) -> bool:
    """"kel gaplashamiz", "suhbatlashaylik", "давай поговорим", "let's talk" …"""
    return _has_phrase(text, _CONVERSATION_START)


def ends_conversation(text: str) -> bool:
    """"bo'ldi, rahmat", "suhbatni tugat", "xayr" …"""
    return _has_phrase(text, _CONVERSATION_STOP)


def levenshtein(a: str, b: str, limit: int | None = None) -> int:
    """Levenshtein masofasi; `limit` berilsa undan oshgach hisoblashni to'xtatadi (limit+1 qaytaradi)."""
    if limit is not None and abs(len(a) - len(b)) > limit:
        return limit + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        if limit is not None and min(current) > limit:
            return limit + 1
        previous = current
    return previous[-1]


def tolerance(name: str) -> int:
    """Qisqa ism aniq mos kelishi kerak; uzunroq ism 2-3 xatoni ko'taradi."""
    n = len(name)
    if n <= 4:
        return 1
    return 2 if n <= 7 else 3


def _candidates(words: list[str]) -> list[tuple[str, int, int]]:
    """(nomzod, boshlanish indeksi, so'zlar soni) — yakka so'zlar va qo'shni juftliklar."""
    out = [(w, i, 1) for i, w in enumerate(words)]
    out += [(a + b, i, 2) for i, (a, b) in enumerate(pairwise(words))]
    return out


def name_in(text: str, name: str) -> bool:
    """Matnda ism (yumshoq moslik bilan) bormi?"""
    target = normalise(name).replace(" ", "")
    if not target:
        return False
    words = normalise(text).split()
    limit = tolerance(target)
    return any(levenshtein(cand, target, limit) <= limit for cand, _, _ in _candidates(words))


def strip_name(text: str, name: str) -> str:
    """Matndan ismni (va oldidagi "hey/salom/ey" kabi undovni) olib tashlaydi.

    Asl matn qaytariladi (normalise qilinmagan), faqat mos kelgan so'zlar o'chiriladi."""
    target = normalise(name).replace(" ", "")
    if not target or not text:
        return text
    limit = tolerance(target)
    raw_words = text.split()
    norm_words = [normalise(w).replace(" ", "") for w in raw_words]
    drop: set[int] = set()
    for cand, start, n in _candidates(norm_words):
        if cand and levenshtein(cand, target, limit) <= limit:
            drop.update(range(start, start + n))
    if not drop:
        return text
    # Ism oldidagi undov so'zlar
    for i in sorted(drop):
        if i - 1 >= 0 and norm_words[i - 1] in ("hey", "ey", "hoy", "salom", "ok", "okay", "эй", "привет"):
            drop.add(i - 1)
    kept = [w for i, w in enumerate(raw_words) if i not in drop]
    out = " ".join(kept).strip(" ,.!?;:")
    return out.strip()


def looks_like_command(text: str) -> bool:
    """SMART rejimi uchun evristika: qisqa gap + buyruq so'zi."""
    norm = normalise(text)
    words = norm.split()
    if not words or len(words) > _SMART_MAX_WORDS:
        return False
    padded = f" {norm} "
    return any(f" {normalise(h).strip()} " in padded for h in _COMMAND_HINTS)


@dataclass
class WakeState:
    """Yordamchi hozir unga gapirilayotganini kuzatadi."""

    name: str = "Nexus"
    mode: str = NAME  # standart: faqat ism bilan chaqirilganda (xonadagi boshqa ovozlarga javob bermaydi)
    follow_up_s: float = DEFAULT_FOLLOW_UP_S
    conversation_idle_s: float = DEFAULT_CONVERSATION_IDLE_S
    conversation: bool = False  # suhbat rejimi ("kel gaplashamiz")
    _called_at: float = field(default=0.0, repr=False)

    def __post_init__(self) -> None:
        self.set_mode(self.mode)
        self.name = (self.name or "").strip()

    # --- sozlash ---
    def set_mode(self, mode: str) -> None:
        m = (mode or "").strip().lower()
        self.mode = m if m in MODES else ALWAYS

    def set_name(self, name: str) -> None:
        self.name = (name or "").strip()

    # --- holat ---
    @property
    def engaged(self) -> bool:
        """Oxirgi chaqiruvdan keyingi oyna (follow-up yoki suhbat) hali ochiqmi?"""
        if not self._called_at:
            return False
        window = self.conversation_idle_s if self.conversation else self.follow_up_s
        return (time.monotonic() - self._called_at) < window

    def start_conversation(self) -> None:
        self.conversation = True
        self._called_at = time.monotonic()

    def stop_conversation(self, follow_up: bool = False) -> None:
        """`follow_up` — aniq tugatilganda oddiy follow-up oynasi qoladi (xayrlashuv javobi eshitilsin)."""
        self.conversation = False
        self._called_at = time.monotonic() if follow_up else 0.0

    @property
    def conversation_expired(self) -> bool:
        """Suhbat rejimi yoqilgan, lekin `conversation_idle_s` jimlikdan keyin tugashi kerak."""
        return self.conversation and not self.engaged

    def heard(self, text: str) -> bool:
        """Matnda ism bormi? Bo'lsa follow-up oynasi ochiladi."""
        if not self.name:
            return False
        if name_in(text, self.name):
            self._called_at = time.monotonic()
            return True
        return False

    def touch(self) -> None:
        """Oynani yangilash — yordamchi hozirgina foydalanuvchi uchun nimadir qildi."""
        if self._called_at:
            self._called_at = time.monotonic()

    def release(self) -> None:
        self._called_at = 0.0

    def should_act(self, text: str) -> bool:
        """Bu gapga javob berish kerakmi? (ism eshitilsa oynani ham ochadi)."""
        if self.conversation and self.engaged:
            if text.strip():
                self._called_at = time.monotonic()  # gapirilyapti — suhbat davom etadi
            return True
        if self.mode == ALWAYS or not self.name:
            return True
        if self.heard(text):
            return True
        if self.engaged:
            return True
        if self.mode == SMART:
            return looks_like_command(text)
        return False

    def strip_name(self, text: str) -> str:
        return strip_name(text, self.name) if self.name else text
