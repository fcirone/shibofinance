"""Tests for the BBVA Uruguay importers (bank PDF + card PDF)."""
from datetime import date
from pathlib import Path

import pytest

import importers.bbva_uy  # noqa: F401 — registers importers
from importers import registry

SAMPLES = Path("/data/samples/bbva_uy")
BANK_PDF = SAMPLES / "conta_bbva.pdf"
CARD_PDF = SAMPLES / "cartao_bbva.pdf"
INST_ID = "test-bbva-bank"
CARD_ID = "test-bbva-card"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bank_bytes():
    return BANK_PDF.read_bytes()


@pytest.fixture(scope="module")
def card_bytes():
    return CARD_PDF.read_bytes()


@pytest.fixture(scope="module")
def bank_result(bank_bytes):
    imp = registry.detect(bank_bytes, BANK_PDF.name, source_hint="bbva_uy")
    return imp.parse(bank_bytes, INST_ID)


@pytest.fixture(scope="module")
def card_result(card_bytes):
    imp = registry.detect(card_bytes, CARD_PDF.name, source_hint="bbva_uy")
    return imp.parse(card_bytes, CARD_ID)


# ---------------------------------------------------------------------------
# Bank detection
# ---------------------------------------------------------------------------


def test_bank_detect(bank_bytes):
    imp = registry.detect(bank_bytes, BANK_PDF.name, source_hint="bbva_uy")
    assert imp.SOURCE_NAME == "bbva_uy_bank"


def test_bank_not_detected_as_card(bank_bytes):
    from importers.bbva_uy.card_parser_pdf import BbvaUyCardImporter
    assert not BbvaUyCardImporter().detect(bank_bytes, BANK_PDF.name)


# ---------------------------------------------------------------------------
# Bank parsing
# ---------------------------------------------------------------------------


def test_bank_parse_returns_transactions(bank_result):
    assert len(bank_result.bank_transactions) > 0


def test_bank_no_card_transactions(bank_result):
    assert bank_result.card_transactions == []


def test_bank_transaction_fields(bank_result):
    tx = bank_result.bank_transactions[0]
    assert tx.posted_date is not None
    assert tx.description_raw != ""
    assert tx.currency in ("UYU", "USD")
    assert tx.fingerprint_hash != ""


def test_bank_has_uyu_transactions(bank_result):
    uyu = [tx for tx in bank_result.bank_transactions if tx.currency == "UYU"]
    assert len(uyu) > 0


def test_bank_has_usd_transactions(bank_result):
    usd = [tx for tx in bank_result.bank_transactions if tx.currency == "USD"]
    assert len(usd) > 0


def test_bank_has_debits_and_credits(bank_result):
    uyu = [tx for tx in bank_result.bank_transactions if tx.currency == "UYU"]
    assert any(tx.amount_minor < 0 for tx in uyu)
    assert any(tx.amount_minor > 0 for tx in uyu)


def test_bank_fingerprints_unique(bank_result):
    fps = [tx.fingerprint_hash for tx in bank_result.bank_transactions]
    assert len(fps) == len(set(fps))


def test_bank_idempotent(bank_bytes):
    imp = registry.detect(bank_bytes, BANK_PDF.name, source_hint="bbva_uy")
    r1 = imp.parse(bank_bytes, INST_ID)
    r2 = imp.parse(bank_bytes, INST_ID)
    fps1 = {tx.fingerprint_hash for tx in r1.bank_transactions}
    fps2 = {tx.fingerprint_hash for tx in r2.bank_transactions}
    assert fps1 == fps2


# ---------------------------------------------------------------------------
# Card detection
# ---------------------------------------------------------------------------


def test_card_detect(card_bytes):
    imp = registry.detect(card_bytes, CARD_PDF.name, source_hint="bbva_uy")
    assert imp.SOURCE_NAME == "bbva_uy_card"


def test_card_not_detected_as_bank(card_bytes):
    from importers.bbva_uy.bank_parser_pdf import BbvaUyBankImporter
    assert not BbvaUyBankImporter().detect(card_bytes, CARD_PDF.name)


# ---------------------------------------------------------------------------
# Card statement
# ---------------------------------------------------------------------------


def test_card_parse_statement(card_result):
    assert len(card_result.card_statements) == 1


def test_card_statement_fields(card_result):
    s = card_result.card_statements[0]
    assert s.due_date is not None
    assert s.closing_date is not None
    assert s.total_minor > 0
    assert s.currency == "UYU"
    assert s.statement_start < s.statement_end


def test_card_statement_due_date(card_result):
    s = card_result.card_statements[0]
    assert s.due_date == date(2026, 3, 12)


def test_card_statement_closing_date(card_result):
    s = card_result.card_statements[0]
    assert s.closing_date == date(2026, 2, 26)


def test_card_statement_total(card_result):
    s = card_result.card_statements[0]
    assert s.total_minor == 1909185  # UYU 19,091.85


# ---------------------------------------------------------------------------
# Card transactions
# ---------------------------------------------------------------------------


def test_card_parse_transactions(card_result):
    assert len(card_result.card_transactions) > 0


def test_card_transaction_fields(card_result):
    tx = card_result.card_transactions[0]
    assert tx.posted_date is not None
    assert tx.description_raw != ""
    assert tx.currency in ("UYU", "USD")
    assert tx.amount_minor > 0
    assert tx.fingerprint_hash != ""


def test_card_has_uyu_and_usd_transactions(card_result):
    uyu = [tx for tx in card_result.card_transactions if tx.currency == "UYU"]
    usd = [tx for tx in card_result.card_transactions if tx.currency == "USD"]
    assert len(uyu) > 0
    assert len(usd) > 0


def test_card_no_negative_amounts(card_result):
    assert all(tx.amount_minor > 0 for tx in card_result.card_transactions)


def test_card_installment_parsed(card_result):
    installments = [tx for tx in card_result.card_transactions if tx.installments_total is not None]
    assert len(installments) > 0
    tx = installments[0]
    assert tx.installment_number is not None
    assert tx.installments_total > 1


def test_card_fingerprints_unique(card_result):
    fps = [tx.fingerprint_hash for tx in card_result.card_transactions]
    assert len(fps) == len(set(fps))


def test_card_idempotent(card_bytes):
    imp = registry.detect(card_bytes, CARD_PDF.name, source_hint="bbva_uy")
    r1 = imp.parse(card_bytes, CARD_ID)
    r2 = imp.parse(card_bytes, CARD_ID)
    fps1 = {tx.fingerprint_hash for tx in r1.card_transactions}
    fps2 = {tx.fingerprint_hash for tx in r2.card_transactions}
    assert fps1 == fps2
