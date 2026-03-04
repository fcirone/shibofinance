"""Orchestrates the full import pipeline.

Pipeline:
  1. Detect importer
  2. Parse rows
  3. Upsert transactions idempotently
  4. Create or update statements
  5. Attempt automatic statement payment matching (delegated to statement_matcher)
"""
import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CreditCard,
    CreditCardStatement,
    ImportBatch,
    ImportStatus,
    Instrument,
    InstrumentType,
    StatementStatus,
)
from app.services.dedupe_service import upsert_bank_transactions, upsert_card_transactions
from importers import registry
from importers.base import CardStatementRow


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def _get_or_create_statement(
    session: AsyncSession,
    credit_card_id: uuid.UUID,
    row: CardStatementRow,
    batch: ImportBatch,
) -> CreditCardStatement:
    stmt = await session.scalar(
        select(CreditCardStatement).where(
            CreditCardStatement.credit_card_id == credit_card_id,
            CreditCardStatement.statement_start == row.statement_start,
            CreditCardStatement.statement_end == row.statement_end,
        )
    )
    if stmt:
        stmt.total_minor = row.total_minor
        stmt.closing_date = row.closing_date
        stmt.due_date = row.due_date
        stmt.raw_payload = row.raw_payload
        return stmt

    stmt = CreditCardStatement(
        credit_card_id=credit_card_id,
        statement_start=row.statement_start,
        statement_end=row.statement_end,
        closing_date=row.closing_date,
        due_date=row.due_date,
        total_minor=row.total_minor,
        currency=row.currency,
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload=row.raw_payload,
    )
    session.add(stmt)
    return stmt


async def run_import(
    session: AsyncSession,
    instrument: Instrument,
    file_bytes: bytes,
    filename: str,
) -> ImportBatch:
    """Run the full import pipeline for a single file.

    Returns the completed ImportBatch with counts populated.
    """
    sha256 = _sha256(file_bytes)

    # Create import batch
    batch = ImportBatch(
        instrument_id=instrument.id,
        filename=filename,
        sha256=sha256,
        status=ImportStatus.created,
    )
    session.add(batch)
    await session.flush()  # get batch.id

    try:
        importer = registry.detect(file_bytes, filename)
        result = importer.parse(file_bytes, str(instrument.id), instrument.metadata_ or {})

        inserted_total = 0
        duplicate_total = 0

        if instrument.type == InstrumentType.bank_account:
            ins, dup = await upsert_bank_transactions(
                session, result.bank_transactions, instrument.id, batch
            )
            inserted_total += ins
            duplicate_total += dup

        elif instrument.type == InstrumentType.credit_card:
            credit_card = await session.scalar(
                select(CreditCard).where(CreditCard.instrument_id == instrument.id)
            )
            if credit_card is None:
                raise ValueError(f"No credit_card record for instrument {instrument.id}")

            # Upsert statements first
            for stmt_row in result.card_statements:
                await _get_or_create_statement(session, credit_card.id, stmt_row, batch)

            ins, dup = await upsert_card_transactions(
                session, result.card_transactions, credit_card.id, batch
            )
            inserted_total += ins
            duplicate_total += dup

        batch.status = ImportStatus.processed
        batch.inserted_count = inserted_total
        batch.duplicate_count = duplicate_total
        batch.processed_at = datetime.now(tz=timezone.utc)

    except Exception:
        batch.status = ImportStatus.failed
        batch.error_count = 1
        raise

    return batch
