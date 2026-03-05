"""Tests for the XP BR importers (bank PDF + card PDF)."""
from pathlib import Path

import pytest

import importers.xp_br  # noqa: F401 — registers importers
from importers import registry

SAMPLES = Path("/data/samples/xp_br")
BANK_PDF = SAMPLES / "conta_xp.pdf"
CARD_PDF = SAMPLES / "cartao_xp.pdf"
CARD_PASSWORD = "29232"
INST_ID = "test-xp-inst"
CARD_ID = "test-xp-card"


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
    imp = registry.detect(bank_bytes, BANK_PDF.name, source_hint="xp_br")
    return imp.parse(bank_bytes, INST_ID)


@pytest.fixture(scope="module")
def card_result(card_bytes):
    imp = registry.detect(card_bytes, CARD_PDF.name, source_hint="xp_br")
    return imp.parse(card_bytes, CARD_ID, {"pdf_password": CARD_PASSWORD})


# ---------------------------------------------------------------------------
# Bank detection
# ---------------------------------------------------------------------------


def test_bank_detect(bank_bytes):
    imp = registry.detect(bank_bytes, BANK_PDF.name, source_hint="xp_br")
    assert imp.SOURCE_NAME == "xp_br_bank"


def test_bank_not_detected_as_card(bank_bytes):
    from importers.xp_br.card_parser_pdf import XpBrCardImporter
    assert not XpBrCardImporter().detect(bank_bytes, BANK_PDF.name)


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
    assert tx.currency == "BRL"
    assert tx.fingerprint_hash != ""


def test_bank_debit_is_negative(bank_result):
    debits = [tx for tx in bank_result.bank_transactions if "enviado" in tx.description_raw.lower()
              or "enviada" in tx.description_raw.lower()]
    assert all(tx.amount_minor < 0 for tx in debits)


def test_bank_credit_is_positive(bank_result):
    credits = [tx for tx in bank_result.bank_transactions if "recebida" in tx.description_raw.lower()
               or "recebido" in tx.description_raw.lower()]
    assert all(tx.amount_minor > 0 for tx in credits)


def test_bank_fingerprints_unique(bank_result):
    fps = [tx.fingerprint_hash for tx in bank_result.bank_transactions]
    assert len(fps) == len(set(fps))


def test_bank_idempotent(bank_bytes):
    imp = registry.detect(bank_bytes, BANK_PDF.name, source_hint="xp_br")
    r1 = imp.parse(bank_bytes, INST_ID)
    r2 = imp.parse(bank_bytes, INST_ID)
    fps1 = {tx.fingerprint_hash for tx in r1.bank_transactions}
    fps2 = {tx.fingerprint_hash for tx in r2.bank_transactions}
    assert fps1 == fps2


# ---------------------------------------------------------------------------
# Card detection
# ---------------------------------------------------------------------------


def test_card_detect(card_bytes):
    imp = registry.detect(card_bytes, CARD_PDF.name, source_hint="xp_br")
    assert imp.SOURCE_NAME == "xp_br_card"


def test_card_bank_not_detected_as_bank(card_bytes):
    from importers.xp_br.bank_parser_pdf import XpBrBankImporter
    assert not XpBrBankImporter().detect(card_bytes, CARD_PDF.name)


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
    assert s.currency == "BRL"
    assert s.statement_start < s.statement_end


def test_card_statement_due_date(card_result):
    from datetime import date
    s = card_result.card_statements[0]
    assert s.due_date == date(2026, 3, 10)


def test_card_statement_total(card_result):
    s = card_result.card_statements[0]
    assert s.total_minor == 891264  # R$ 8.912,64


# ---------------------------------------------------------------------------
# Card transactions
# ---------------------------------------------------------------------------


def test_card_parse_transactions(card_result):
    assert len(card_result.card_transactions) > 0


def test_card_transaction_fields(card_result):
    tx = card_result.card_transactions[0]
    assert tx.posted_date is not None
    assert tx.description_raw != ""
    assert tx.currency == "BRL"
    assert tx.amount_minor > 0
    assert tx.fingerprint_hash != ""


def test_card_installment_parsed(card_result):
    installments = [tx for tx in card_result.card_transactions if tx.installments_total is not None]
    assert len(installments) > 0
    tx = installments[0]
    assert tx.installment_number is not None
    assert tx.installments_total > 1


def test_card_no_negative_amounts(card_result):
    # Payments/credits should be filtered out
    assert all(tx.amount_minor > 0 for tx in card_result.card_transactions)


def test_card_fingerprints_unique(card_result):
    fps = [tx.fingerprint_hash for tx in card_result.card_transactions]
    assert len(fps) == len(set(fps))


def test_card_wrong_password_raises(card_bytes):
    from importers.xp_br.card_parser_pdf import XpBrCardImporter
    with pytest.raises(ValueError, match="Could not decrypt"):
        XpBrCardImporter().parse(card_bytes, CARD_ID, {"pdf_password": "wrong"})
