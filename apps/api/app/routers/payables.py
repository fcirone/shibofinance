"""Payables and recurring patterns endpoints."""
import calendar
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import (
    OccurrenceStatus,
    Payable,
    PayableOccurrence,
    PayableSourceType,
    RecurringPattern,
    RecurringPatternStatus,
)
from app.schemas import (
    DetectResult,
    GenerateOccurrencesRequest,
    GenerateOccurrencesResult,
    OccurrenceUpdate,
    PayableCreate,
    PayableOccurrenceOut,
    PayableOut,
    RecurringPatternCreate,
    RecurringPatternOut,
)
from app.services.recurring_detection import detect_recurring_patterns

router = APIRouter(tags=["payables"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pattern_out(p: RecurringPattern) -> RecurringPatternOut:
    return RecurringPatternOut(
        id=p.id,
        name=p.name,
        normalized_description=p.normalized_description,
        category_id=p.category_id,
        category_name=p.category.name if p.category else None,
        expected_amount_minor=p.expected_amount_minor,
        cadence=p.cadence,
        detection_source=p.detection_source,
        status=p.status,
        created_at=p.created_at,
    )


def _payable_out(p: Payable) -> PayableOut:
    return PayableOut(
        id=p.id,
        name=p.name,
        category_id=p.category_id,
        category_name=p.category.name if p.category else None,
        default_amount_minor=p.default_amount_minor,
        notes=p.notes,
        source_type=p.source_type,
        recurring_pattern_id=p.recurring_pattern_id,
        created_at=p.created_at,
    )


def _occurrence_out(o: PayableOccurrence) -> PayableOccurrenceOut:
    return PayableOccurrenceOut(
        id=o.id,
        payable_id=o.payable_id,
        payable_name=o.payable.name,
        due_date=o.due_date,
        expected_amount_minor=o.expected_amount_minor,
        actual_amount_minor=o.actual_amount_minor,
        status=o.status,
        notes=o.notes,
        created_at=o.created_at,
    )


# ---------------------------------------------------------------------------
# Recurring patterns
# ---------------------------------------------------------------------------


@router.get("/recurring-patterns", response_model=list[RecurringPatternOut])
async def list_recurring_patterns(
    status: RecurringPatternStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(RecurringPattern).options(selectinload(RecurringPattern.category))
    if status is not None:
        q = q.where(RecurringPattern.status == status)
    q = q.order_by(RecurringPattern.created_at.desc())
    patterns = (await db.scalars(q)).all()
    return [_pattern_out(p) for p in patterns]


@router.post("/recurring-patterns", response_model=RecurringPatternOut, status_code=status.HTTP_201_CREATED)
async def create_recurring_pattern(body: RecurringPatternCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(
        select(RecurringPattern).where(RecurringPattern.normalized_description == body.normalized_description)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Pattern with this normalized description already exists")
    from app.models import DetectionSource, RecurringPatternStatus as RPS
    pattern = RecurringPattern(
        name=body.name,
        normalized_description=body.normalized_description,
        category_id=body.category_id,
        expected_amount_minor=body.expected_amount_minor,
        cadence=body.cadence,
        detection_source=DetectionSource.manual,
        status=RPS.approved,
    )
    db.add(pattern)
    await db.commit()
    pattern = await db.scalar(
        select(RecurringPattern)
        .where(RecurringPattern.id == pattern.id)
        .options(selectinload(RecurringPattern.category))
    )
    return _pattern_out(pattern)


@router.post("/recurring-patterns/detect", response_model=DetectResult)
async def run_detection(db: AsyncSession = Depends(get_db)):
    created, skipped = await detect_recurring_patterns(db)
    return DetectResult(created=created, skipped=skipped)


@router.post("/recurring-patterns/{pattern_id}/approve", response_model=RecurringPatternOut)
async def approve_pattern(pattern_id: str, db: AsyncSession = Depends(get_db)):
    pattern = await db.scalar(
        select(RecurringPattern)
        .where(RecurringPattern.id == pattern_id)
        .options(selectinload(RecurringPattern.category))
    )
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    pattern.status = RecurringPatternStatus.approved
    await db.commit()
    await db.refresh(pattern)
    return _pattern_out(pattern)


@router.post("/recurring-patterns/{pattern_id}/ignore", response_model=RecurringPatternOut)
async def ignore_pattern(pattern_id: str, db: AsyncSession = Depends(get_db)):
    pattern = await db.scalar(
        select(RecurringPattern)
        .where(RecurringPattern.id == pattern_id)
        .options(selectinload(RecurringPattern.category))
    )
    if not pattern:
        raise HTTPException(status_code=404, detail="Recurring pattern not found")
    pattern.status = RecurringPatternStatus.ignored
    await db.commit()
    await db.refresh(pattern)
    return _pattern_out(pattern)


# ---------------------------------------------------------------------------
# Payables
# ---------------------------------------------------------------------------


@router.get("/payables", response_model=list[PayableOut])
async def list_payables(db: AsyncSession = Depends(get_db)):
    payables = (
        await db.scalars(
            select(Payable)
            .options(selectinload(Payable.category))
            .order_by(Payable.name)
        )
    ).all()
    return [_payable_out(p) for p in payables]


@router.post("/payables", response_model=PayableOut, status_code=status.HTTP_201_CREATED)
async def create_payable(body: PayableCreate, db: AsyncSession = Depends(get_db)):
    payable = Payable(
        name=body.name,
        category_id=body.category_id,
        default_amount_minor=body.default_amount_minor,
        notes=body.notes,
        source_type=PayableSourceType.manual,
    )
    db.add(payable)
    await db.commit()
    payable = await db.scalar(
        select(Payable)
        .where(Payable.id == payable.id)
        .options(selectinload(Payable.category))
    )
    return _payable_out(payable)


# ---------------------------------------------------------------------------
# Payable occurrences
# ---------------------------------------------------------------------------


@router.get("/payable-occurrences", response_model=list[PayableOccurrenceOut])
async def list_occurrences(
    month: int | None = None,
    year: int | None = None,
    status: OccurrenceStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(PayableOccurrence)
        .options(selectinload(PayableOccurrence.payable))
        .order_by(PayableOccurrence.due_date)
    )
    if month is not None and year is not None:
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
        q = q.where(PayableOccurrence.due_date >= first, PayableOccurrence.due_date <= last)
    if status is not None:
        q = q.where(PayableOccurrence.status == status)
    occurrences = (await db.scalars(q)).all()
    return [_occurrence_out(o) for o in occurrences]


@router.post("/payable-occurrences/generate", response_model=GenerateOccurrencesResult)
async def generate_occurrences(body: GenerateOccurrencesRequest, db: AsyncSession = Depends(get_db)):
    if body.month < 1 or body.month > 12:
        raise HTTPException(status_code=422, detail="month must be between 1 and 12")

    due_date = date(body.year, body.month, calendar.monthrange(body.year, body.month)[1])

    # Fetch all payables
    payables = (
        await db.scalars(select(Payable).options(selectinload(Payable.occurrences)))
    ).all()

    created = 0
    skipped = 0

    for payable in payables:
        # Check if occurrence already exists for this month/year
        already_exists = any(
            o.due_date.year == body.year and o.due_date.month == body.month
            for o in payable.occurrences
        )
        if already_exists:
            skipped += 1
            continue

        occurrence = PayableOccurrence(
            payable_id=payable.id,
            due_date=due_date,
            expected_amount_minor=payable.default_amount_minor or 0,
            status=OccurrenceStatus.expected,
        )
        db.add(occurrence)
        created += 1

    await db.commit()
    return GenerateOccurrencesResult(created=created, skipped=skipped)


@router.patch("/payable-occurrences/{occurrence_id}", response_model=PayableOccurrenceOut)
async def update_occurrence(
    occurrence_id: str,
    body: OccurrenceUpdate,
    db: AsyncSession = Depends(get_db),
):
    occurrence = await db.scalar(
        select(PayableOccurrence)
        .where(PayableOccurrence.id == occurrence_id)
        .options(selectinload(PayableOccurrence.payable))
    )
    if not occurrence:
        raise HTTPException(status_code=404, detail="Occurrence not found")

    if body.status is not None:
        occurrence.status = body.status
    if body.actual_amount_minor is not None:
        occurrence.actual_amount_minor = body.actual_amount_minor
    if body.notes is not None:
        occurrence.notes = body.notes

    await db.commit()
    await db.refresh(occurrence)
    return _occurrence_out(occurrence)
