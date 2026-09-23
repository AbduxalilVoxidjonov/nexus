"""Wake (ism bilan chaqirish) va diktovka mantiqi testlari."""
from __future__ import annotations

import pytest

from nexus import wake as wake_mod
from nexus.dictation import DictationState, is_stop_phrase, split_stop
from nexus.wake import (
    ALWAYS,
    NAME,
    SMART,
    WakeState,
    levenshtein,
    looks_like_command,
    name_in,
    normalise,
    strip_name,
    tolerance,
)


# ---------------------------------------------------------------------------
# normalise / levenshtein / tolerance
# ---------------------------------------------------------------------------
def test_normalise_folds_case_apostrophes_and_cyrillic():
    assert normalise("O'zbek, ozbek!") == "ozbek  ozbek "
    assert normalise("Нексус") == "neksus"
    assert normalise("Héllo") == "hello"
    assert normalise("") == ""


@pytest.mark.parametrize(
    "a,b,d",
    [("nexus", "nexus", 0), ("nexus", "neksus", 2), ("nexus", "nex", 2), ("", "abc", 3), ("kitten", "sitting", 3)],
)
def test_levenshtein(a, b, d):
    assert levenshtein(a, b) == d


def test_levenshtein_limit_short_circuits():
    assert levenshtein("abcdefgh", "zzzzzzzz", limit=2) == 3
    assert levenshtein("abc", "abcdefgh", limit=2) == 3  # uzunlik farqi > limit


def test_tolerance_by_length():
    assert tolerance("luna") == 1
    assert tolerance("nexus") == 2
    assert tolerance("jarvis1") == 2
    assert tolerance("assistant") == 3


# ---------------------------------------------------------------------------
# name_in / strip_name
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,expected",
    [
        ("nexus", True),
        ("Nexus!", True),
        ("neksus", True),
        ("нексус", True),
        ("hey nexus ovozni ko'tar", True),
        ("Neksus, Safarini och", True),
        ("nek sus, salom", True),  # ikkiga bo'lingan ism (qo'shni juftlik)
        ("salom, qalaysan", False),
        ("Safarini och", False),
        ("", False),
    ],
)
def test_name_in_nexus(text, expected):
    assert name_in(text, "Nexus") is expected


def test_name_in_short_name_is_strict():
    assert name_in("luna, salom", "Luna") is True
    assert name_in("lunar", "Luna") is True  # 1 xato
    assert name_in("lu", "Luna") is False  # 2 xato — qisqa ism uchun ko'p
    assert name_in("salom", "") is False


def test_name_in_two_word_name():
    assert name_in("hey jarvis bot, och", "Jarvis Bot") is True
    assert name_in("jarvisbot och", "Jarvis Bot") is True


@pytest.mark.parametrize(
    "text,expected",
    [
        ("hey nexus ovozni ko'tar", "ovozni ko'tar"),
        ("Nexus, Safarini och", "Safarini och"),
        ("Safarini och, Neksus", "Safarini och"),
        ("rahmat nexus", "rahmat"),
        ("salom nexus", ""),  # undov + ism — ikkalasi olib tashlanadi
        ("Safarini och", "Safarini och"),
        ("nexus", ""),
        ("", ""),
    ],
)
def test_strip_name(text, expected):
    assert strip_name(text, "Nexus") == expected


def test_looks_like_command():
    assert looks_like_command("Safarini och") is True
    assert looks_like_command("открой браузер") is True
    assert looks_like_command("volume up please") is True
    assert looks_like_command("kecha biz juda uzoq gaplashdik va u och qoldi degan edi menimcha uyda") is False
    assert looks_like_command("qalaysan bugun") is False
    assert looks_like_command("") is False


# ---------------------------------------------------------------------------
# WakeState — rejimlar va follow-up oynasi
# ---------------------------------------------------------------------------
@pytest.fixture
def clock(monkeypatch):
    t = [1000.0]
    monkeypatch.setattr(wake_mod.time, "monotonic", lambda: t[0])
    return t


def test_wake_always_mode_acts_on_everything(clock):
    w = WakeState(name="Nexus", mode=ALWAYS)
    assert w.should_act("Safarini och") is True
    assert w.should_act("") is True
    assert w.engaged is False  # always rejimida oyna ochilmaydi (ism qidirilmaydi)


def test_wake_name_mode_requires_name_then_follow_up(clock):
    w = WakeState(name="Nexus", mode=NAME, follow_up_s=25)
    assert w.should_act("Safarini och") is False
    assert w.engaged is False
    assert w.should_act("Neksus, Safarini och") is True
    assert w.engaged is True
    clock[0] += 10
    assert w.should_act("endi yop") is True  # follow-up oynasi ochiq
    assert w.should_act("") is True
    clock[0] += 20  # 30 s — oxirgi chaqiruvdan (touch bo'lmagan) oyna yopildi
    assert w.engaged is False
    assert w.should_act("endi yop") is False


def test_wake_touch_extends_window_and_release_closes(clock):
    w = WakeState(name="Nexus", mode=NAME, follow_up_s=25)
    w.touch()  # chaqiruv bo'lmagan — hech narsa qilmaydi
    assert w.engaged is False
    assert w.should_act("nexus") is True
    clock[0] += 20
    w.touch()  # tool bajarildi — oyna yangilandi
    clock[0] += 20
    assert w.engaged is True  # 40 s o'tdi, lekin touch 20 s da bo'lgan
    w.release()
    assert w.engaged is False
    assert w.should_act("davom et") is False


def test_wake_smart_mode(clock):
    w = WakeState(name="Nexus", mode=SMART, follow_up_s=25)
    assert w.should_act("Safarini och") is True  # buyruqqa o'xshaydi
    assert w.engaged is False  # ism aytilmadi — oyna ochilmadi
    assert w.should_act("kecha biz uzoq gaplashdik va u och qoldi degan edi menimcha uyda") is False
    assert w.should_act("qalaysan bugun") is False
    assert w.should_act("nexus qalaysan bugun") is True
    assert w.should_act("qalaysan bugun") is True  # oyna ochiq


def test_wake_no_name_acts_always(clock):
    w = WakeState(name="", mode=NAME)
    assert w.should_act("nimadir") is True


def test_wake_set_mode_and_name():
    w = WakeState(name=" Nexus ", mode="XATO")
    assert w.mode == ALWAYS and w.name == "Nexus"
    w.set_mode("Name")
    assert w.mode == NAME
    w.set_name("Luna")
    assert w.name == "Luna"
    assert w.strip_name("Luna, salom") == "salom"


# ---------------------------------------------------------------------------
# Diktovka — split_stop
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,expected",
    [
        ("to'xta", ("", True)),
        ("To'xtat!", ("", True)),
        ("bas", ("", True)),
        ("Bas.", ("", True)),
        ("tugat", ("", True)),
        ("yetarli", ("", True)),
        ("shu yetarli", ("", True)),
        ("stop", ("", True)),
        ("стоп", ("", True)),
        ("Хватит.", ("", True)),
        ("yozishni to'xtat", ("", True)),
        ("hammasi shu, to'xta", ("hammasi shu", True)),
        ("Assalomu alaykum. Stop", ("Assalomu alaykum", True)),
        ("bu oxirgi jumla bas", ("bu oxirgi jumla", True)),
        ("это всё, хватит", ("это всё", True)),
        ("basketbol o'ynaymiz", ("basketbol o'ynaymiz", False)),
        ("bas qilmasdan davom etaylik", ("bas qilmasdan davom etaylik", False)),
        ("to'xtash joyida kutdim", ("to'xtash joyida kutdim", False)),
        ("stop so'zi gap o'rtasida bo'lsa terilaveradi", ("stop so'zi gap o'rtasida bo'lsa terilaveradi", False)),
        ("davom etamiz", ("davom etamiz", False)),
        ("", ("", False)),
        ("   ", ("", False)),
    ],
)
def test_split_stop(text, expected):
    assert split_stop(text) == expected


def test_is_stop_phrase():
    assert is_stop_phrase("To'xta") is True
    assert is_stop_phrase("toxta") is True  # apostrofsiz transkript
    assert is_stop_phrase("to'xta endi") is False
    assert is_stop_phrase("") is False


def test_dictation_state_lifecycle(monkeypatch):
    t = [50.0]
    import nexus.dictation as dm

    monkeypatch.setattr(dm.time, "monotonic", lambda: t[0])
    d = DictationState()
    assert d.active is False and d.duration_s == 0.0
    d.start()
    assert d.active is True
    d.note_typed("salom")
    d.note_typed("dunyo")
    assert d.typed_chars == 10 and d.buffer == ["salom", "dunyo"]
    t[0] += 3
    assert d.duration_s == 3.0
    assert d.split_stop("shu, bas") == ("shu", True)
    assert d.is_stop_phrase("bas") is True
    d.stop()
    assert d.active is False
    d.start()
    assert d.typed_chars == 0 and d.buffer == []
