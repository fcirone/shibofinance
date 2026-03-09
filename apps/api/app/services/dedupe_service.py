"""Idempotent upsert logic for bank and card transactions."""
import uuid
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BankTransaction, CreditCardTransaction, ImportBatch
from importers.base import BankTransactionRow, CardTransactionRow


async def upsert_bank_transactions(
    session: AsyncSession,
    rows: list[BankTransactionRow],
    instrument_id: uuid.UUID,
    batch: ImportBatch,
) -> tuple[int, int, list[uuid.UUID]]:
    """Insert new bank transactions, skip duplicates.

    Returns (inserted_count, duplicate_count, inserted_ids).
    """
    inserted = 0
    duplicates = 0
    inserted_ids: list[uuid.UUID] = []

    for row in rows:
        existing = await session.scalar(
            select(BankTransaction).where(BankTransaction.fingerprint_hash == row.fingerprint_hash)
        )
        if existing:
            duplicates += 1
            continue

        tx = BankTransaction(
            instrument_id=instrument_id,
            posted_at=row.posted_at.replace(tzinfo=timezone.utc) if row.posted_at.tzinfo is None else row.posted_at,
            posted_date=row.posted_date,
            description_raw=row.description_raw,
            description_norm=row.description_norm,
            amount_minor=row.amount_minor,
            currency=row.currency,
            source_tx_id=row.source_tx_id,
            fingerprint_hash=row.fingerprint_hash,
            import_batch_id=batch.id,
            raw_payload=row.raw_payload,
        )
        session.add(tx)
        await session.flush()
        inserted_ids.append(tx.id)
        inserted += 1

    return inserted, duplicates, inserted_ids


async def upsert_card_transactions(
    session: AsyncSession,
    rows: list[CardTransactionRow],
    credit_card_id: uuid.UUID,
    batch: ImportBatch,
) -> tuple[int, int, list[uuid.UUID]]:
    """Insert new card transactions, skip duplicates.

    Returns (inserted_count, duplicate_count, inserted_ids).
    """
    inserted = 0
    duplicates = 0
    inserted_ids: list[uuid.UUID] = []

    for row in rows:
        existing = await session.scalar(
            select(CreditCardTransaction).where(
                CreditCardTransaction.fingerprint_hash == row.fingerprint_hash
            )
        )
        if existing:
            duplicates += 1
            continue

        tx = CreditCardTransaction(
            credit_card_id=credit_card_id,
            posted_at=row.posted_at.replace(tzinfo=timezone.utc) if row.posted_at.tzinfo is None else row.posted_at,
            posted_date=row.posted_date,
            description_raw=row.description_raw,
            description_norm=row.description_norm,
            merchant_raw=row.merchant_raw,
            amount_minor=row.amount_minor,
            currency=row.currency,
            installments_total=row.installments_total,
            installment_number=row.installment_number,
            source_tx_id=row.source_tx_id,
            fingerprint_hash=row.fingerprint_hash,
            import_batch_id=batch.id,
            raw_payload=row.raw_payload,
        )
        session.add(tx)
        await session.flush()
        inserted_ids.append(tx.id)
        inserted += 1

    return inserted, duplicates, inserted_ids
