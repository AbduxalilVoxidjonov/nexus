"""Umumiy test sozlamalari."""
from __future__ import annotations

import sys

import pytest

POSIX_ONLY = pytest.mark.skipif(sys.platform == "win32", reason="POSIX/macOS'ga xos xatti-harakat")


@pytest.fixture(autouse=True)
def _registry_as_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registry testlari OS'dan mustaqil: Windows'da ham to'liq (macOS) tool ro'yxati bilan ishlaydi.

    Windows filtri `tests/test_windows.py` da `IS_WINDOWS=True` qo'yib alohida tekshiriladi.
    """
    from nexus.tools import registry

    monkeypatch.setattr(registry, "IS_WINDOWS", False)
