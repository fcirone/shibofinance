from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Categorization, Category
from app.schemas import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(select(Category).order_by(Category.name))
    return rows.all()


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(body: CategoryCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(select(Category).where(Category.name == body.name))
    if existing:
        raise HTTPException(status_code=409, detail="Category name already exists")
    if body.parent_id:
        parent = await db.get(Category, body.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
    cat = Category(name=body.name, kind=body.kind, parent_id=body.parent_id)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: str,
    body: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    cat = await db.get(Category, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    if body.name is not None:
        existing = await db.scalar(select(Category).where(Category.name == body.name))
        if existing and existing.id != cat.id:
            raise HTTPException(status_code=409, detail="Category name already exists")
        cat.name = body.name
    if body.kind is not None:
        cat.kind = body.kind
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db)):
    cat = await db.get(Category, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    in_use = await db.scalar(
        select(Categorization).where(Categorization.category_id == cat.id)
    )
    if in_use:
        raise HTTPException(
            status_code=409, detail="Category is in use and cannot be deleted"
        )
    await db.delete(cat)
    await db.commit()
