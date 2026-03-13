"""Portfolio summary, snapshot, and history calculations."""
from collections import defaultdict
from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    AssetClass,
    AssetPosition,
    InvestmentAccount,
    PortfolioSnapshot,
    PortfolioSnapshotItem,
)
from app.schemas import (
    AccountSummaryItem,
    AllocationItem,
    AssetHistoryPoint,
    PortfolioHistoryPoint,
    PortfolioSummaryOut,
)


async def get_portfolio_summary(db: AsyncSession) -> PortfolioSummaryOut:
    result = await db.execute(
        select(InvestmentAccount).options(
            selectinload(InvestmentAccount.positions).selectinload(AssetPosition.asset)
        )
    )
    accounts = result.scalars().all()

    account_summaries: list[AccountSummaryItem] = []
    class_totals: dict[AssetClass, int] = defaultdict(int)
    grand_total = 0

    for account in accounts:
        account_total = sum(
            (pos.current_value_minor or 0) for pos in account.positions
        )
        account_summaries.append(
            AccountSummaryItem(
                account_id=account.id,
                account_name=account.name,
                currency=account.currency,
                total_value_minor=account_total,
            )
        )
        grand_total += account_total
        for pos in account.positions:
            class_totals[pos.asset.asset_class] += pos.current_value_minor or 0

    allocation: list[AllocationItem] = []
    for asset_class, total in sorted(class_totals.items(), key=lambda x: x[1], reverse=True):
        pct = round(total / grand_total * 100, 2) if grand_total > 0 else 0.0
        allocation.append(AllocationItem(asset_class=asset_class, total_value_minor=total, pct=pct))

    return PortfolioSummaryOut(
        total_value_minor=grand_total,
        accounts=account_summaries,
        allocation=allocation,
    )


async def _positions_as_of(db: AsyncSession, snapshot_date: date) -> list[AssetPosition]:
    """Return the most recent position for each (account, asset) pair where as_of_date <= snapshot_date."""
    # Subquery: for each (account, asset) pair, find the latest as_of_date up to snapshot_date
    subq = (
        select(
            AssetPosition.investment_account_id,
            AssetPosition.asset_id,
            func.max(AssetPosition.as_of_date).label("max_date"),
        )
        .where(AssetPosition.as_of_date <= snapshot_date)
        .group_by(AssetPosition.investment_account_id, AssetPosition.asset_id)
        .subquery()
    )

    q = (
        select(AssetPosition)
        .options(selectinload(AssetPosition.asset))
        .join(
            subq,
            (AssetPosition.investment_account_id == subq.c.investment_account_id)
            & (AssetPosition.asset_id == subq.c.asset_id)
            & (AssetPosition.as_of_date == subq.c.max_date),
        )
    )
    result = await db.execute(q)
    return result.scalars().all()


async def upsert_snapshot_for_date(db: AsyncSession, snapshot_date: date) -> PortfolioSnapshot:
    """Create or update a snapshot for a specific date.

    Uses the most recent position for each (account, asset) pair with
    as_of_date <= snapshot_date, so each snapshot reflects the portfolio
    state known as of that date.
    """
    positions = await _positions_as_of(db, snapshot_date)
    grand_total = sum(pos.current_value_minor or 0 for pos in positions)

    # Upsert snapshot record for this date
    snapshot = await db.scalar(
        select(PortfolioSnapshot).where(PortfolioSnapshot.snapshot_date == snapshot_date)
    )
    if snapshot is None:
        snapshot = PortfolioSnapshot(
            snapshot_date=snapshot_date,
            total_value_minor=grand_total,
            currency="BRL",
        )
        db.add(snapshot)
        await db.flush()
    else:
        snapshot.total_value_minor = grand_total
        await db.flush()

    # Replace snapshot items for this date
    await db.execute(
        delete(PortfolioSnapshotItem).where(PortfolioSnapshotItem.snapshot_id == snapshot.id)
    )
    for pos in positions:
        db.add(PortfolioSnapshotItem(
            snapshot_id=snapshot.id,
            asset_id=pos.asset_id,
            investment_account_id=pos.investment_account_id,
            asset_name=pos.asset.name,
            asset_symbol=pos.asset.symbol,
            asset_class=pos.asset.asset_class,
            quantity=pos.quantity,
            current_value_minor=pos.current_value_minor or 0,
        ))

    await db.commit()

    # Eagerly reload so callers can access .items without lazy loading
    result_snap = await db.execute(
        select(PortfolioSnapshot)
        .options(selectinload(PortfolioSnapshot.items))
        .where(PortfolioSnapshot.id == snapshot.id)
    )
    return result_snap.scalar_one()


# Keep old name as alias for the manual "record today" endpoint
async def upsert_daily_snapshot(db: AsyncSession) -> PortfolioSnapshot:
    return await upsert_snapshot_for_date(db, date.today())


async def rebuild_snapshot_history(db: AsyncSession) -> int:
    """Delete all snapshots and rebuild one per distinct position as_of_date.

    Returns the number of snapshots created.
    """
    # Get all distinct as_of_dates that have at least one position
    result = await db.execute(
        select(AssetPosition.as_of_date).distinct().order_by(AssetPosition.as_of_date)
    )
    dates = result.scalars().all()

    # Wipe all existing snapshots (cascade deletes items via FK)
    await db.execute(delete(PortfolioSnapshot))
    await db.flush()

    # Rebuild one snapshot per date
    for d in dates:
        await upsert_snapshot_for_date(db, d)

    return len(dates)


async def get_portfolio_history(
    db: AsyncSession,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[PortfolioHistoryPoint]:
    """Return total portfolio value over time."""
    q = select(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_date)
    if date_from:
        q = q.where(PortfolioSnapshot.snapshot_date >= date_from)
    if date_to:
        q = q.where(PortfolioSnapshot.snapshot_date <= date_to)
    result = await db.execute(q)
    return [
        PortfolioHistoryPoint(
            snapshot_date=s.snapshot_date,
            total_value_minor=s.total_value_minor,
            currency=s.currency,
        )
        for s in result.scalars().all()
    ]


async def get_asset_history(
    db: AsyncSession,
    asset_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[AssetHistoryPoint]:
    """Return value of a specific asset over time (from snapshot items)."""
    q = (
        select(PortfolioSnapshotItem, PortfolioSnapshot.snapshot_date)
        .join(PortfolioSnapshot, PortfolioSnapshotItem.snapshot_id == PortfolioSnapshot.id)
        .where(PortfolioSnapshotItem.asset_id == asset_id)
        .order_by(PortfolioSnapshot.snapshot_date)
    )
    if date_from:
        q = q.where(PortfolioSnapshot.snapshot_date >= date_from)
    if date_to:
        q = q.where(PortfolioSnapshot.snapshot_date <= date_to)

    result = await db.execute(q)
    rows = result.all()

    # Group by date — sum if same asset appears in multiple accounts
    by_date: dict[date, AssetHistoryPoint] = {}
    for item, snap_date in rows:
        if snap_date not in by_date:
            by_date[snap_date] = AssetHistoryPoint(
                snapshot_date=snap_date,
                asset_id=str(item.asset_id),
                asset_name=item.asset_name,
                asset_symbol=item.asset_symbol,
                asset_class=item.asset_class,
                quantity=item.quantity,
                current_value_minor=item.current_value_minor,
            )
        else:
            by_date[snap_date].quantity += item.quantity
            by_date[snap_date].current_value_minor += item.current_value_minor

    return list(by_date.values())
