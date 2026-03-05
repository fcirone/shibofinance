import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import ImportBatch, Instrument
from app.schemas import ImportBatchOut
from app.services.import_service import run_import

router = APIRouter(prefix="/imports", tags=["imports"])


@router.get("", response_model=list[ImportBatchOut])
async def list_import_batches(
    instrument_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    q = select(ImportBatch).order_by(ImportBatch.created_at.desc())
    if instrument_id:
        q = q.where(ImportBatch.instrument_id == instrument_id)
    q = q.limit(limit).offset(offset)
    rows = await db.scalars(q)
    return rows.all()


@router.get("/{batch_id}", response_model=ImportBatchOut)
async def get_import_batch(
    batch_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    batch = await db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")
    return batch


@router.post("/upload", response_model=ImportBatchOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    instrument_id: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    inst = await db.get(Instrument, instrument_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")

    file_bytes = await file.read()
    try:
        batch = await run_import(db, inst, file_bytes, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    await db.commit()
    await db.refresh(batch)
    return batch
