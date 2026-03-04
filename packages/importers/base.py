"""Base importer interface and shared result types."""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol


@dataclass
class BankTransactionRow:
    posted_at: datetime          # UTC-aware
    posted_date: date
    description_raw: str
    description_norm: str
    amount_minor: int
    currency: str
    source_tx_id: str | None
    fingerprint_hash: str
    raw_payload: dict


@dataclass
class CardTransactionRow:
    posted_at: datetime          # UTC-aware
    posted_date: date
    description_raw: str
    description_norm: str
    merchant_raw: str | None
    amount_minor: int
    currency: str
    installments_total: int | None
    installment_number: int | None
    source_tx_id: str | None
    fingerprint_hash: str
    raw_payload: dict


@dataclass
class CardStatementRow:
    statement_start: date
    statement_end: date
    closing_date: date | None
    due_date: date | None
    total_minor: int
    currency: str
    raw_payload: dict


@dataclass
class ImportResult:
    bank_transactions: list[BankTransactionRow] = field(default_factory=list)
    card_transactions: list[CardTransactionRow] = field(default_factory=list)
    card_statements: list[CardStatementRow] = field(default_factory=list)


class BaseImporter(Protocol):
    SOURCE_NAME: str

    def detect(self, file_bytes: bytes, filename: str) -> bool:
        """Return True if this importer can handle the given file."""
        ...

    def parse(
        self,
        file_bytes: bytes,
        instrument_id: str,
        instrument_metadata: dict | None = None,
    ) -> ImportResult:
        """Parse the file and return normalised rows."""
        ...
