"""Pydantic v2 request/response schemas."""
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import (
    CategorizationSource,
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


class InstrumentUpdate(BaseModel):
    name: str | None = None
    metadata_: dict[str, Any] | None = None


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
    category_id: uuid.UUID | None = None
    category_name: str | None = None


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
    category_id: uuid.UUID | None = None
    category_name: str | None = None


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: CategoryKind
    parent_id: uuid.UUID | None


class CategoryCreate(BaseModel):
    name: str
    kind: CategoryKind
    parent_id: uuid.UUID | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    kind: CategoryKind | None = None


class CategorizeRequest(BaseModel):
    target_type: TargetType
    target_id: uuid.UUID
    category_id: uuid.UUID
    confidence: float | None = None
    source: CategorizationSource = CategorizationSource.manual


class CategorizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_type: TargetType
    target_id: uuid.UUID
    category_id: uuid.UUID
    confidence: float | None
    source: CategorizationSource
    created_at: datetime


class BulkCategorizeRequest(BaseModel):
    items: list[CategorizeRequest]


class BulkCategorizeResult(BaseModel):
    updated: int
    created: int


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
