from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Categorization, Category
from app.schemas import (
    BulkCategorizeRequest,
    BulkCategorizeResult,
    CategorizeRequest,
    CategorizationOut,
)

router = APIRouter(tags=["categorizations"])


@router.post("/categorize", response_model=CategorizationOut, status_code=status.HTTP_201_CREATED)
async def categorize(body: CategorizeRequest, db: AsyncSession = Depends(get_db)):
    cat = await db.get(Category, body.category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    existing = await db.scalar(
        select(Categorization).where(
            Categorization.target_type == body.target_type,
            Categorization.target_id == body.target_id,
        )
    )
    if existing:
        existing.category_id = body.category_id
        existing.confidence = body.confidence
        existing.source = body.source
        await db.commit()
        await db.refresh(existing)
        return existing

    categ = Categorization(
        target_type=body.target_type,
        target_id=body.target_id,
        category_id=body.category_id,
        confidence=body.confidence,
        source=body.source,
    )
    db.add(categ)
    await db.commit()
    await db.refresh(categ)
    return categ


@router.post("/categorize/bulk", response_model=BulkCategorizeResult)
async def categorize_bulk(body: BulkCategorizeRequest, db: AsyncSession = Depends(get_db)):
    updated = 0
    created = 0
    for item in body.items:
        cat = await db.get(Category, item.category_id)
        if not cat:
            raise HTTPException(status_code=404, detail=f"Category {item.category_id} not found")
        existing = await db.scalar(
            select(Categorization).where(
                Categorization.target_type == item.target_type,
                Categorization.target_id == item.target_id,
            )
        )
        if existing:
            existing.category_id = item.category_id
            existing.confidence = item.confidence
            existing.source = item.source
            updated += 1
        else:
            db.add(Categorization(
                target_type=item.target_type,
                target_id=item.target_id,
                category_id=item.category_id,
                confidence=item.confidence,
                source=item.source,
            ))
            created += 1
    await db.commit()
    return BulkCategorizeResult(updated=updated, created=created)


@router.delete("/categorizations/{categorization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_categorization(
    categorization_id: str, db: AsyncSession = Depends(get_db)
):
    categ = await db.get(Categorization, categorization_id)
    if not categ:
        raise HTTPException(status_code=404, detail="Categorization not found")
    await db.delete(categ)
    await db.commit()
