"""Portfolio summary and allocation calculations."""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AssetClass, AssetPosition, InvestmentAccount
from app.schemas import AccountSummaryItem, AllocationItem, PortfolioSummaryOut


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
