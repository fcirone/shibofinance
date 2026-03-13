"""Investment accounts, assets, positions, and portfolio history endpoints."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Asset, AssetPosition, InvestmentAccount
from app.schemas import (
    AssetCreate,
    AssetHistoryPoint,
    AssetOut,
    AssetPositionCreate,
    AssetPositionOut,
    AssetPositionUpdate,
    InvestmentAccountCreate,
    InvestmentAccountOut,
    PortfolioHistoryPoint,
    PortfolioSummaryOut,
    SnapshotOut,
)
from app.services.portfolio_service import (
    get_asset_history,
    get_portfolio_history,
    get_portfolio_summary,
    upsert_daily_snapshot,
    upsert_snapshot_for_date,
)

router = APIRouter(tags=["investments"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _position_out(pos: AssetPosition) -> AssetPositionOut:
    return AssetPositionOut(
        id=pos.id,
        investment_account_id=pos.investment_account_id,
        asset_id=pos.asset_id,
        asset_symbol=pos.asset.symbol,
        asset_name=pos.asset.name,
        asset_class=pos.asset.asset_class,
        quantity=pos.quantity,
        average_cost_minor=pos.average_cost_minor,
        current_value_minor=pos.current_value_minor,
        as_of_date=pos.as_of_date,
        created_at=pos.created_at,
    )


# ---------------------------------------------------------------------------
# Investment Accounts
# ---------------------------------------------------------------------------


@router.get("/investment-accounts", response_model=list[InvestmentAccountOut])
async def list_investment_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvestmentAccount).order_by(InvestmentAccount.name))
    return result.scalars().all()


@router.post("/investment-accounts", response_model=InvestmentAccountOut, status_code=status.HTTP_201_CREATED)
async def create_investment_account(
    body: InvestmentAccountCreate,
    db: AsyncSession = Depends(get_db),
):
    account = InvestmentAccount(
        name=body.name,
        institution_name=body.institution_name,
        currency=body.currency.upper(),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


@router.get("/assets", response_model=list[AssetOut])
async def list_assets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).order_by(Asset.name))
    return result.scalars().all()


@router.post("/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
async def create_asset(
    body: AssetCreate,
    db: AsyncSession = Depends(get_db),
):
    asset = Asset(
        symbol=body.symbol,
        name=body.name,
        asset_class=body.asset_class,
        currency=body.currency.upper(),
        metadata_=body.metadata,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


# ---------------------------------------------------------------------------
# Asset Positions
# ---------------------------------------------------------------------------


@router.get("/asset-positions", response_model=list[AssetPositionOut])
async def list_asset_positions(
    investment_account_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(AssetPosition).options(selectinload(AssetPosition.asset))
    if investment_account_id:
        q = q.where(AssetPosition.investment_account_id == investment_account_id)
    q = q.order_by(AssetPosition.as_of_date.desc())
    result = await db.execute(q)
    positions = result.scalars().all()
    return [_position_out(p) for p in positions]


@router.post("/asset-positions", response_model=AssetPositionOut, status_code=status.HTTP_201_CREATED)
async def create_asset_position(
    body: AssetPositionCreate,
    db: AsyncSession = Depends(get_db),
):
    account = await db.get(InvestmentAccount, body.investment_account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Investment account not found")
    asset = await db.get(Asset, body.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    pos = AssetPosition(
        investment_account_id=body.investment_account_id,
        asset_id=body.asset_id,
        quantity=body.quantity,
        average_cost_minor=body.average_cost_minor,
        current_value_minor=body.current_value_minor,
        as_of_date=body.as_of_date,
    )
    db.add(pos)
    await db.commit()

    result = await db.execute(
        select(AssetPosition).options(selectinload(AssetPosition.asset)).where(AssetPosition.id == pos.id)
    )
    pos = result.scalar_one()

    # Auto-snapshot using the position's own as_of_date
    await upsert_snapshot_for_date(db, body.as_of_date)

    return _position_out(pos)


@router.patch("/asset-positions/{position_id}", response_model=AssetPositionOut)
async def update_asset_position(
    position_id: uuid.UUID,
    body: AssetPositionUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AssetPosition).options(selectinload(AssetPosition.asset)).where(AssetPosition.id == position_id)
    )
    pos = result.scalar_one_or_none()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")

    if body.quantity is not None:
        pos.quantity = body.quantity
    if body.average_cost_minor is not None:
        pos.average_cost_minor = body.average_cost_minor
    if body.current_value_minor is not None:
        pos.current_value_minor = body.current_value_minor
    if body.as_of_date is not None:
        pos.as_of_date = body.as_of_date

    await db.commit()

    result = await db.execute(
        select(AssetPosition).options(selectinload(AssetPosition.asset)).where(AssetPosition.id == pos.id)
    )
    pos = result.scalar_one()

    # Auto-snapshot using the position's own as_of_date
    await upsert_snapshot_for_date(db, pos.as_of_date)

    return _position_out(pos)


@router.delete("/asset-positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_position(
    position_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    pos = await db.get(AssetPosition, position_id)
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")

    snapshot_date = pos.as_of_date
    await db.delete(pos)
    await db.commit()

    # Rebuild snapshot for the affected date
    await upsert_snapshot_for_date(db, snapshot_date)


# ---------------------------------------------------------------------------
# Portfolio Summary & History
# ---------------------------------------------------------------------------


@router.get("/portfolio/summary", response_model=PortfolioSummaryOut)
async def portfolio_summary(db: AsyncSession = Depends(get_db)):
    return await get_portfolio_summary(db)


@router.post("/portfolio/snapshot", response_model=SnapshotOut, status_code=status.HTTP_201_CREATED)
async def record_portfolio_snapshot(db: AsyncSession = Depends(get_db)):
    """Manually record a snapshot of the current portfolio state."""
    snapshot = await upsert_daily_snapshot(db)
    item_count = len(snapshot.items) if snapshot.items else 0
    return SnapshotOut(
        snapshot_date=snapshot.snapshot_date,
        total_value_minor=snapshot.total_value_minor,
        currency=snapshot.currency,
        item_count=item_count,
    )


@router.get("/portfolio/history", response_model=list[PortfolioHistoryPoint])
async def portfolio_history(
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Total portfolio value over time."""
    return await get_portfolio_history(db, date_from=date_from, date_to=date_to)


@router.get("/portfolio/history/assets", response_model=list[AssetHistoryPoint])
async def asset_history(
    asset_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Value of a specific asset over time."""
    return await get_asset_history(db, str(asset_id), date_from=date_from, date_to=date_to)
