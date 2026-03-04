"""Tests for the importer framework (base, registry)."""
from datetime import date, datetime, timezone

import pytest

from importers.base import (
    BankTransactionRow,
    CardStatementRow,
    CardTransactionRow,
    ImportResult,
)
from importers import registry as reg


# ---------------------------------------------------------------------------
# Helpers — minimal stub importer
# ---------------------------------------------------------------------------

class StubImporter:
    SOURCE_NAME = "stub"

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        return filename.endswith(".stub")

    def parse(self, file_bytes: bytes, instrument_id: str) -> ImportResult:
        return ImportResult(
            bank_transactions=[
                BankTransactionRow(
                    posted_at=datetime(2024, 1, 10, 12, 0, tzinfo=timezone.utc),
                    posted_date=date(2024, 1, 10),
                    description_raw="COMPRA MERCADO",
                    description_norm="compra mercado",
                    amount_minor=-5000,
                    currency="BRL",
                    source_tx_id=None,
                    fingerprint_hash="abc123",
                    raw_payload={"orig": "row"},
                )
            ]
        )


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_register_and_detect():
    # Reset registry for test isolation
    reg._registry.clear()
    stub = StubImporter()
    reg.register(stub)

    detected = reg.detect(b"content", "file.stub")
    assert detected is stub


def test_detect_raises_for_unknown():
    reg._registry.clear()
    reg.register(StubImporter())

    with pytest.raises(ValueError, match="No importer found"):
        reg.detect(b"content", "file.csv")


def test_registered_sources():
    reg._registry.clear()
    reg.register(StubImporter())
    assert reg.registered_sources() == ["stub"]


# ---------------------------------------------------------------------------
# ImportResult defaults
# ---------------------------------------------------------------------------

def test_import_result_defaults():
    result = ImportResult()
    assert result.bank_transactions == []
    assert result.card_transactions == []
    assert result.card_statements == []


# ---------------------------------------------------------------------------
# Row dataclasses
# ---------------------------------------------------------------------------

def test_bank_transaction_row_fields():
    row = BankTransactionRow(
        posted_at=datetime(2024, 3, 1, tzinfo=timezone.utc),
        posted_date=date(2024, 3, 1),
        description_raw="PIX",
        description_norm="pix",
        amount_minor=10000,
        currency="BRL",
        source_tx_id="TX123",
        fingerprint_hash="hash",
        raw_payload={},
    )
    assert row.amount_minor == 10000
    assert row.source_tx_id == "TX123"


def test_card_statement_row_fields():
    row = CardStatementRow(
        statement_start=date(2024, 1, 1),
        statement_end=date(2024, 1, 31),
        closing_date=date(2024, 2, 5),
        due_date=date(2024, 2, 10),
        total_minor=150000,
        currency="BRL",
        raw_payload={},
    )
    assert row.total_minor == 150000
    assert row.due_date == date(2024, 2, 10)
