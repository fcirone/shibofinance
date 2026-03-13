"""Portfolio summary, snapshot, and history calculations."""
from collections import defaultdict
from datetime import date

from sqlalchemy import delete, select
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


async def upsert_daily_snapshot(db: AsyncSession) -> PortfolioSnapshot:
    """Create or update today's portfolio snapshot from current positions."""
    today = date.today()

    # Load all positions with asset + account info
    result = await db.execute(
        select(InvestmentAccount).options(
            selectinload(InvestmentAccount.positions).selectinload(AssetPosition.asset)
        )
    )
    accounts = result.scalars().all()

    grand_total = sum(
        (pos.current_value_minor or 0)
        for account in accounts
        for pos in account.positions
    )

    # Upsert the daily snapshot record
    snapshot = await db.scalar(
        select(PortfolioSnapshot).where(PortfolioSnapshot.snapshot_date == today)
    )
    if snapshot is None:
        snapshot = PortfolioSnapshot(
            snapshot_date=today,
            total_value_minor=grand_total,
            currency="BRL",
        )
        db.add(snapshot)
        await db.flush()
    else:
        snapshot.total_value_minor = grand_total
        await db.flush()

    # Replace snapshot items for today
    await db.execute(
        delete(PortfolioSnapshotItem).where(PortfolioSnapshotItem.snapshot_id == snapshot.id)
    )
    for account in accounts:
        for pos in account.positions:
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

    # Eagerly reload snapshot with items so callers can access .items synchronously
    result_snap = await db.execute(
        select(PortfolioSnapshot)
        .options(selectinload(PortfolioSnapshot.items))
        .where(PortfolioSnapshot.id == snapshot.id)
    )
    return result_snap.scalar_one()


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
