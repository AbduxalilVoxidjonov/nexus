"""Diktovka rejimi: foydalanuvchi gapiradi — yordamchi teradi, to'xtash iborasigacha.

Oddiy rejimda har gap model orqali o'tadi va model nima qilishni hal qiladi.
Diktovkada aksincha: har bir aytilgan gap aynan teriladigan matn, model jim
turadi. Faqat aniq to'xtash iborasi ("to'xta", "bas", "tugat", "yetarli",
"stop", "стоп", "хватит") rejimni tugatadi — u gap OXIRIDA yoki alohida gap
sifatida kelgandagina (gap o'rtasidagi "bas" yoki "basketbol" terilaveradi).

Transkript modelning navbatini kutmasdan to'g'ridan-to'g'ri teriladi: tezroq
(har gap uchun round-trip yo'q), aniq (nima aytilgan bo'lsa shu teriladi) va
model har gapga ovoz chiqarib javob berishga urinmaydi.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from nexus.wake import normalise

# Diktovkani tugatuvchi iboralar (normalise qilingan holda solishtiriladi)
STOP_PHRASES = (
    "to'xta", "to'xtat", "to'xtang", "yozishni to'xtat", "yozishni to'xta",
    "bas", "bas qil", "tugat", "tugatdim", "yetarli", "shu yetarli", "stop", "stop dictation",
    "стоп", "хватит", "закончи", "diktovkani tugat", "diktovkani to'xtat",
)

# Gap OXIRIDAGI to'xtash iborasi (oldida ixtiyoriy vergul/nuqta/bo'shliq)
_STOP_TAIL = re.compile(
    r"(?:^|[\s,.;:!?\-—]+)"
    r"(?:yozishni\s+|diktovkani\s+)?"
    r"(?:to['’ʻʼ`]?xta(?:t|ng|ting)?|bas(?:\s+qil)?|tugat(?:dim|ing)?|(?:shu\s+)?yetarli|stop(?:\s+dictation)?"
    r"|стоп|хватит|закончи)"
    r"[\s,.;:!?\-—]*$",
    re.IGNORECASE | re.UNICODE,
)

_NORMALISED_STOPS = tuple(sorted({" ".join(normalise(p).split()) for p in STOP_PHRASES}))


def is_stop_phrase(text: str) -> bool:
    """Butun gap faqat to'xtash iborasidan iboratmi?"""
    stripped = " ".join(normalise(text).split())
    return bool(stripped) and stripped in _NORMALISED_STOPS


def split_stop(text: str) -> tuple[str, bool]:
    """(teriladigan matn, to'xtash kerakmi).

    "…hammasi shu, to'xta" → ("…hammasi shu", True); "to'xta" → ("", True);
    "bas qilmasdan davom etaylik" → (asl matn, False)."""
    text = (text or "").strip()
    if not text:
        return "", False
    if is_stop_phrase(text):
        return "", True
    trimmed = _STOP_TAIL.sub("", text)
    if trimmed != text:
        return trimmed.strip(" ,.;:!?-—"), True
    return text, False


@dataclass
class DictationState:
    """Diktovka holati va terilgan matn hisobi."""

    active: bool = False
    started_at: float = 0.0
    typed_chars: int = 0
    buffer: list[str] = field(default_factory=list)

    def start(self) -> None:
        self.active = True
        self.started_at = time.monotonic()
        self.typed_chars = 0
        self.buffer.clear()

    def stop(self) -> None:
        self.active = False

    @property
    def duration_s(self) -> float:
        if not self.started_at:
            return 0.0
        return time.monotonic() - self.started_at

    def is_stop_phrase(self, text: str) -> bool:
        return is_stop_phrase(text)

    def split_stop(self, text: str) -> tuple[str, bool]:
        return split_stop(text)

    def note_typed(self, text: str) -> None:
        self.typed_chars += len(text)
        self.buffer.append(text)
        del self.buffer[:-50]
