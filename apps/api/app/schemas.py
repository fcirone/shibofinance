"""Pydantic v2 request/response schemas."""
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import (
    CategoryKind,
    ImportStatus,
    InstrumentSource,
    InstrumentType,
    StatementStatus,
    TargetType,
)


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------


class InstrumentCreate(BaseModel):
    name: str
    type: InstrumentType
    source: InstrumentSource
    currency: str
    source_instrument_id: str = ""
    metadata_: dict[str, Any] | None = None


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: InstrumentType
    source: InstrumentSource
    currency: str
    source_instrument_id: str
    metadata_: dict[str, Any] | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Import batches
# ---------------------------------------------------------------------------


class ImportBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    instrument_id: uuid.UUID
    filename: str
    sha256: str
    status: ImportStatus
    inserted_count: int
    duplicate_count: int
    error_count: int
    created_at: datetime
    processed_at: datetime | None


# ---------------------------------------------------------------------------
# Bank transactions
# ---------------------------------------------------------------------------


class BankTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    instrument_id: uuid.UUID
    posted_date: date
    description_raw: str
    description_norm: str
    amount_minor: int
    currency: str
    fingerprint_hash: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Credit card statements
# ---------------------------------------------------------------------------


class CardStatementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    credit_card_id: uuid.UUID
    statement_start: date
    statement_end: date
    closing_date: date | None
    due_date: date | None
    total_minor: int
    currency: str
    status: StatementStatus
    created_at: datetime


# ---------------------------------------------------------------------------
# Credit card transactions
# ---------------------------------------------------------------------------


class CardTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    credit_card_id: uuid.UUID
    posted_date: date
    description_raw: str
    description_norm: str
    merchant_raw: str | None
    amount_minor: int
    currency: str
    installments_total: int | None
    installment_number: int | None
    fingerprint_hash: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: CategoryKind
    parent_id: uuid.UUID | None


class CategorizeRequest(BaseModel):
    target_type: TargetType
    target_id: uuid.UUID
    category_id: uuid.UUID
    confidence: float | None = None


class CategorizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_type: TargetType
    target_id: uuid.UUID
    category_id: uuid.UUID
    confidence: float | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Spending summary
# ---------------------------------------------------------------------------


class SpendingByCategory(BaseModel):
    category_name: str
    category_kind: CategoryKind
    total_minor: int
    currency: str
    transaction_count: int


class SpendingSummaryOut(BaseModel):
    date_from: date
    date_to: date
    by_category: list[SpendingByCategory]
    uncategorized_minor: int
    total_minor: int
