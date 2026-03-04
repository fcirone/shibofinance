"""Integration tests for the Santander BR importers against real sample files."""
import os
from pathlib import Path

import pytest

SAMPLES_DIR = Path("/data/samples/santander_br")
BANK_PDF = SAMPLES_DIR / "santander_extrato_conta.pdf"
CARD_PDF = SAMPLES_DIR / "santander_cartao.pdf"
CARD_PASSWORD = os.environ.get("SANTANDER_CPF", "29232916894")


def _skip_if_missing(path: Path):
    if not path.exists():
        pytest.skip(f"Sample file not found: {path}")


# --------------------------------------------------------------------------- #
# Bank statement
# --------------------------------------------------------------------------- #


def test_bank_detect():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    imp = SantanderBrBankImporter()
    assert imp.detect(BANK_PDF.read_bytes(), BANK_PDF.name) is True


def test_bank_parse_returns_transactions():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    result = SantanderBrBankImporter().parse(BANK_PDF.read_bytes(), "inst-id")
    assert len(result.bank_transactions) > 50


def test_bank_parse_no_card_transactions():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    result = SantanderBrBankImporter().parse(BANK_PDF.read_bytes(), "inst-id")
    assert result.card_transactions == []
    assert result.card_statements == []


def test_bank_transaction_fields():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    result = SantanderBrBankImporter().parse(BANK_PDF.read_bytes(), "inst-id")
    tx = result.bank_transactions[0]
    assert tx.currency == "BRL"
    assert tx.posted_date.year == 2025
    assert tx.description_raw
    assert tx.description_norm
    assert tx.fingerprint_hash
    assert len(tx.fingerprint_hash) == 64
    assert tx.amount_minor != 0


def test_bank_debit_is_negative():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    result = SantanderBrBankImporter().parse(BANK_PDF.read_bytes(), "inst-id")
    pix_enviados = [t for t in result.bank_transactions if "PIX ENVIADO" in t.description_raw]
    assert pix_enviados
    assert all(t.amount_minor < 0 for t in pix_enviados)


def test_bank_credit_is_positive():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    result = SantanderBrBankImporter().parse(BANK_PDF.read_bytes(), "inst-id")
    pix_recebidos = [t for t in result.bank_transactions if "PIX RECEBIDO" in t.description_raw]
    assert pix_recebidos
    assert all(t.amount_minor > 0 for t in pix_recebidos)


def test_bank_fingerprints_unique():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    result = SantanderBrBankImporter().parse(BANK_PDF.read_bytes(), "inst-id")
    hashes = [t.fingerprint_hash for t in result.bank_transactions]
    assert len(hashes) == len(set(hashes)), "Duplicate fingerprints found"


def test_bank_idempotent():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.bank_parser_pdf import SantanderBrBankImporter

    data = BANK_PDF.read_bytes()
    r1 = SantanderBrBankImporter().parse(data, "inst-id")
    r2 = SantanderBrBankImporter().parse(data, "inst-id")
    hashes1 = {t.fingerprint_hash for t in r1.bank_transactions}
    hashes2 = {t.fingerprint_hash for t in r2.bank_transactions}
    assert hashes1 == hashes2


# --------------------------------------------------------------------------- #
# Credit card statement
# --------------------------------------------------------------------------- #


def test_card_detect():
    _skip_if_missing(CARD_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    imp = SantanderBrCardImporter()
    assert imp.detect(CARD_PDF.read_bytes(), CARD_PDF.name) is True


def test_card_bank_not_detected_as_card():
    _skip_if_missing(BANK_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    imp = SantanderBrCardImporter()
    assert imp.detect(BANK_PDF.read_bytes(), BANK_PDF.name) is False


def test_card_parse_statement():
    _skip_if_missing(CARD_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    meta = {"pdf_password": CARD_PASSWORD}
    result = SantanderBrCardImporter().parse(CARD_PDF.read_bytes(), "inst-id", meta)
    assert len(result.card_statements) == 1
    stmt = result.card_statements[0]
    assert stmt.due_date is not None
    assert stmt.total_minor > 0
    assert stmt.currency == "BRL"


def test_card_parse_transactions():
    _skip_if_missing(CARD_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    meta = {"pdf_password": CARD_PASSWORD}
    result = SantanderBrCardImporter().parse(CARD_PDF.read_bytes(), "inst-id", meta)
    assert len(result.card_transactions) > 50


def test_card_transaction_fields():
    _skip_if_missing(CARD_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    meta = {"pdf_password": CARD_PASSWORD}
    result = SantanderBrCardImporter().parse(CARD_PDF.read_bytes(), "inst-id", meta)
    tx = result.card_transactions[0]
    assert tx.currency == "BRL"
    assert tx.description_raw
    assert tx.fingerprint_hash
    assert len(tx.fingerprint_hash) == 64


def test_card_payment_is_negative():
    _skip_if_missing(CARD_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    meta = {"pdf_password": CARD_PASSWORD}
    result = SantanderBrCardImporter().parse(CARD_PDF.read_bytes(), "inst-id", meta)
    payments = [t for t in result.card_transactions if "PAGAMENTO" in t.description_raw]
    assert payments
    assert all(t.amount_minor < 0 for t in payments)


def test_card_international_brl_amount():
    """International transactions should use the BRL amount, not UYU/USD."""
    _skip_if_missing(CARD_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    meta = {"pdf_password": CARD_PASSWORD}
    result = SantanderBrCardImporter().parse(CARD_PDF.read_bytes(), "inst-id", meta)
    brothaus = next((t for t in result.card_transactions if "BROTHAUS" in t.description_raw), None)
    assert brothaus is not None
    assert brothaus.amount_minor == 47701  # R$ 477,01


def test_card_fingerprints_unique():
    _skip_if_missing(CARD_PDF)
    from importers.santander_br.card_parser_pdf import SantanderBrCardImporter

    meta = {"pdf_password": CARD_PASSWORD}
    result = SantanderBrCardImporter().parse(CARD_PDF.read_bytes(), "inst-id", meta)
    hashes = [t.fingerprint_hash for t in result.card_transactions]
    assert len(hashes) == len(set(hashes)), "Duplicate fingerprints found"
