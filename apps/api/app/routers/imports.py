from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Instrument
from app.schemas import ImportBatchOut
from app.services.import_service import run_import

router = APIRouter(prefix="/imports", tags=["imports"])


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
