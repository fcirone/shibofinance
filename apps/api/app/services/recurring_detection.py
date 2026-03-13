"""Recurring transaction detection heuristics."""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BankTransaction,
    CreditCardTransaction,
    DetectionSource,
    RecurringCadence,
    RecurringPattern,
    RecurringPatternStatus,
)

_MIN_DISTINCT_MONTHS = 2
_MIN_OCCURRENCES = 3


def _infer_cadence(dates: list[date]) -> RecurringCadence:
    if len(dates) < 2:
        return RecurringCadence.custom
    sorted_dates = sorted(dates)
    gaps = [(sorted_dates[i + 1] - sorted_dates[i]).days for i in range(len(sorted_dates) - 1)]
    avg_gap = sum(gaps) / len(gaps)
    if 25 <= avg_gap <= 35:
        return RecurringCadence.monthly
    if 6 <= avg_gap <= 8:
        return RecurringCadence.weekly
    if 350 <= avg_gap <= 380:
        return RecurringCadence.yearly
    return RecurringCadence.custom


async def detect_recurring_patterns(db: AsyncSession) -> tuple[int, int]:
    """Analyse transactions and create suggested recurring patterns.

    Returns (created, skipped) counts.
    """
    # Existing normalized descriptions — skip to avoid duplicates
    existing_descs: set[str] = set(
        (await db.scalars(select(RecurringPattern.normalized_description))).all()
    )

    # Collect (description_norm, posted_date, abs_amount) from both tx types
    desc_data: dict[str, list[tuple[date, int]]] = defaultdict(list)

    bank_rows = (
        await db.execute(
            select(BankTransaction.description_norm, BankTransaction.posted_date, BankTransaction.amount_minor)
            .where(BankTransaction.amount_minor < 0)
        )
    ).all()
    for desc, dt, amt in bank_rows:
        desc_data[desc].append((dt, abs(amt)))

    card_rows = (
        await db.execute(
            select(
                CreditCardTransaction.description_norm,
                CreditCardTransaction.posted_date,
                CreditCardTransaction.amount_minor,
            )
            .where(CreditCardTransaction.amount_minor > 0)
        )
    ).all()
    for desc, dt, amt in card_rows:
        desc_data[desc].append((dt, amt))

    created = 0
    skipped = 0

    for desc_norm, entries in desc_data.items():
        if desc_norm in existing_descs:
            skipped += 1
            continue

        dates = [e[0] for e in entries]
        amounts = [e[1] for e in entries]

        distinct_months = len({(d.year, d.month) for d in dates})
        if distinct_months < _MIN_DISTINCT_MONTHS or len(entries) < _MIN_OCCURRENCES:
            skipped += 1
            continue

        cadence = _infer_cadence(dates)
        median_amount = int(statistics.median(amounts))

        # Build a human-readable name from the normalized description
        name = desc_norm.title()[:100]

        pattern = RecurringPattern(
            name=name,
            normalized_description=desc_norm,
            expected_amount_minor=median_amount,
            cadence=cadence,
            detection_source=DetectionSource.system,
            status=RecurringPatternStatus.suggested,
        )
        db.add(pattern)
        existing_descs.add(desc_norm)
        created += 1

    if created:
        await db.commit()

    return created, skipped
