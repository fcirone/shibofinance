from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Categorization, Category
from app.schemas import CategorizeRequest, CategorizationOut, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Category).order_by(Category.name))
    return rows.all()


@router.post("/categorize", response_model=CategorizationOut, status_code=status.HTTP_201_CREATED)
async def categorize(body: CategorizeRequest, db: AsyncSession = Depends(get_db)):
    cat = await db.get(Category, body.category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    # Upsert: update if exists
    existing = await db.scalar(
        select(Categorization).where(
            Categorization.target_type == body.target_type,
            Categorization.target_id == body.target_id,
        )
    )
    if existing:
        existing.category_id = body.category_id
        existing.confidence = body.confidence
        await db.commit()
        await db.refresh(existing)
        return existing

    categ = Categorization(
        target_type=body.target_type,
        target_id=body.target_id,
        category_id=body.category_id,
        confidence=body.confidence,
    )
    db.add(categ)
    await db.commit()
    await db.refresh(categ)
    return categ
