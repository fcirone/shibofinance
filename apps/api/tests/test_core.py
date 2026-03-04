"""Tests for packages/core modules (money, timezones, normalizers, fingerprint)."""
from datetime import date, datetime
from decimal import Decimal

import pytest

from core.money import from_minor, to_minor
from core.normalizers import normalize_description
from core.fingerprint import compute_fingerprint
from core.timezones import TZ_BRAZIL, TZ_URUGUAY, TZ_UTC, to_utc


# ---------------------------------------------------------------------------
# money
# ---------------------------------------------------------------------------


def test_to_minor_basic():
    assert to_minor("100.50") == 10050


def test_to_minor_negative():
    assert to_minor("-3.99") == -399


def test_to_minor_zero():
    assert to_minor("0.00") == 0


def test_to_minor_float():
    assert to_minor(1.005) == 101  # rounds half-up


def test_from_minor_basic():
    assert from_minor(10050) == Decimal("100.50")


def test_from_minor_negative():
    assert from_minor(-399) == Decimal("-3.99")


def test_roundtrip():
    assert from_minor(to_minor("250.75")) == Decimal("250.75")


# ---------------------------------------------------------------------------
# normalizers
# ---------------------------------------------------------------------------


def test_normalize_lowercase():
    assert normalize_description("COMPRA SUPERMERCADO") == "compra supermercado"


def test_normalize_accents():
    assert normalize_description("Pagamento João") == "pagamento joao"


def test_normalize_collapse_whitespace():
    assert normalize_description("foo   bar") == "foo bar"


def test_normalize_duplicate_punctuation():
    assert normalize_description("foo,,bar") == "foo,bar"


def test_normalize_combined():
    result = normalize_description("  PÁGTÕ   CARTÃO,,  ")
    assert result == "pagto cartao,"


# ---------------------------------------------------------------------------
# fingerprint
# ---------------------------------------------------------------------------

_INST = "abc-123"
_DATE = date(2024, 1, 15)
_CURRENCY = "BRL"
_AMOUNT = 10050
_DESC = "compra supermercado"


def test_fingerprint_is_hex_64():
    h = compute_fingerprint(_INST, _DATE, _CURRENCY, _AMOUNT, _DESC)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_fingerprint_deterministic():
    h1 = compute_fingerprint(_INST, _DATE, _CURRENCY, _AMOUNT, _DESC)
    h2 = compute_fingerprint(_INST, _DATE, _CURRENCY, _AMOUNT, _DESC)
    assert h1 == h2


def test_fingerprint_changes_with_amount():
    h1 = compute_fingerprint(_INST, _DATE, _CURRENCY, _AMOUNT, _DESC)
    h2 = compute_fingerprint(_INST, _DATE, _CURRENCY, _AMOUNT + 1, _DESC)
    assert h1 != h2


def test_fingerprint_changes_with_description():
    h1 = compute_fingerprint(_INST, _DATE, _CURRENCY, _AMOUNT, _DESC)
    h2 = compute_fingerprint(_INST, _DATE, _CURRENCY, _AMOUNT, _DESC + "x")
    assert h1 != h2


# ---------------------------------------------------------------------------
# timezones
# ---------------------------------------------------------------------------


def test_to_utc_brazil_naive():
    naive = datetime(2024, 3, 15, 10, 0, 0)
    utc = to_utc(naive, "santander_br")
    assert utc.tzinfo == TZ_UTC
    # BRT = UTC-3, so 10:00 BRT -> 13:00 UTC
    assert utc.hour == 13


def test_to_utc_uruguay_naive():
    naive = datetime(2024, 3, 15, 10, 0, 0)
    utc = to_utc(naive, "bbva_uy")
    assert utc.tzinfo == TZ_UTC
    # UYT = UTC-3, so 10:00 UYT -> 13:00 UTC
    assert utc.hour == 13


def test_to_utc_already_aware():
    aware = datetime(2024, 3, 15, 10, 0, 0, tzinfo=TZ_BRAZIL)
    utc = to_utc(aware, "santander_br")
    assert utc.tzinfo == TZ_UTC
