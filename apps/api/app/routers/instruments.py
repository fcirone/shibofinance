from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import CreditCard, Instrument, InstrumentType
from app.schemas import InstrumentCreate, InstrumentOut, InstrumentUpdate

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.post("", response_model=InstrumentOut, status_code=status.HTTP_201_CREATED)
async def create_instrument(body: InstrumentCreate, db: AsyncSession = Depends(get_db)):
    inst = Instrument(
        name=body.name,
        type=body.type,
        source=body.source,
        currency=body.currency,
        source_instrument_id=body.source_instrument_id,
        metadata_=body.metadata_,
    )
    db.add(inst)
    await db.flush()

    # Auto-create credit_card row for credit card instruments
    if inst.type == InstrumentType.credit_card:
        db.add(CreditCard(instrument_id=inst.id, statement_currency=inst.currency))

    await db.commit()
    await db.refresh(inst)
    return inst


@router.get("", response_model=list[InstrumentOut])
async def list_instruments(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Instrument).order_by(Instrument.created_at))
    return rows.all()


@router.get("/{instrument_id}", response_model=InstrumentOut)
async def get_instrument(instrument_id: str, db: AsyncSession = Depends(get_db)):
    inst = await db.get(Instrument, instrument_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return inst


@router.patch("/{instrument_id}", response_model=InstrumentOut)
async def update_instrument(
    instrument_id: str, body: InstrumentUpdate, db: AsyncSession = Depends(get_db)
):
    inst = await db.get(Instrument, instrument_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")
    if body.name is not None:
        inst.name = body.name
    if body.metadata_ is not None:
        inst.metadata_ = body.metadata_
    await db.commit()
    await db.refresh(inst)
    return inst
