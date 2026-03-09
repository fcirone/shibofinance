"""Categorization rule engine.

Evaluates enabled category rules against uncategorized (or rule-categorized)
transactions. Manual categorizations are never overwritten.
"""
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    BankTransaction,
    CategorizationEvent,
    CategorizationSource,
    Categorization,
    CategoryRule,
    CreditCardTransaction,
    EventAction,
    MatchField,
    MatchOperator,
    RuleTargetType,
    TargetType,
)

# ---------------------------------------------------------------------------
# Validation helpers (used by the router too)
# ---------------------------------------------------------------------------

VALID_COMBOS: dict[MatchField, set[MatchOperator]] = {
    MatchField.description_raw:  {MatchOperator.contains, MatchOperator.equals, MatchOperator.regex},
    MatchField.description_norm: {MatchOperator.contains, MatchOperator.equals, MatchOperator.regex},
    MatchField.merchant_raw:     {MatchOperator.contains, MatchOperator.equals, MatchOperator.regex},
    MatchField.amount_minor:     {MatchOperator.equals, MatchOperator.gte, MatchOperator.lte},
}

BATCH_SIZE = 500


def rule_label(rule: CategoryRule) -> str:
    """Human-readable description of a rule for tooltip display."""
    return f"{rule.match_field.value} {rule.match_operator.value} '{rule.match_value}'"


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def _get_field_value(tx: BankTransaction | CreditCardTransaction, field: MatchField) -> str | int | None:
    if field == MatchField.description_raw:
        return tx.description_raw
    if field == MatchField.description_norm:
        return tx.description_norm
    if field == MatchField.merchant_raw:
        return getattr(tx, "merchant_raw", None)
    if field == MatchField.amount_minor:
        return tx.amount_minor
    return None


def _matches(rule: CategoryRule, tx: BankTransaction | CreditCardTransaction) -> bool:
    value = _get_field_value(tx, rule.match_field)
    if value is None:
        return False

    mv = rule.match_value
    op = rule.match_operator

    if op == MatchOperator.contains:
        return mv.lower() in str(value).lower()
    if op == MatchOperator.equals:
        if isinstance(value, int):
            try:
                return value == int(mv)
            except ValueError:
                return False
        return str(value).lower() == mv.lower()
    if op == MatchOperator.regex:
        try:
            return bool(re.search(mv, str(value), re.IGNORECASE))
        except re.error:
            return False
    if op == MatchOperator.gte:
        try:
            return int(value) >= int(mv)
        except (ValueError, TypeError):
            return False
    if op == MatchOperator.lte:
        try:
            return int(value) <= int(mv)
        except (ValueError, TypeError):
            return False
    return False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


async def apply_rules(
    session: AsyncSession,
    transaction_ids: list[uuid.UUID] | None = None,
    dry_run: bool = False,
) -> dict:
    """Evaluate all enabled rules against uncategorized/rule-categorized transactions.

    Args:
        session: DB session (caller manages commit).
        transaction_ids: If provided, scope evaluation to only these IDs.
        dry_run: If True, compute matches without writing to DB.

    Returns:
        {"applied": int, "by_category": [{"category_name": str, "count": int}]}
    """
    rules = (await session.scalars(
        select(CategoryRule)
        .options(selectinload(CategoryRule.category))
        .where(CategoryRule.enabled.is_(True))
        .order_by(CategoryRule.priority)
    )).all()

    if not rules:
        return {"applied": 0, "by_category": []}

    counts: dict[str, int] = defaultdict(int)  # category_name → count
    total = 0

    for target_type in (TargetType.bank_transaction, TargetType.card_transaction):
        applicable_rules = [
            r for r in rules
            if r.target_type == RuleTargetType.both
            or r.target_type.value == target_type.value
        ]
        if not applicable_rules:
            continue

        Model = BankTransaction if target_type == TargetType.bank_transaction else CreditCardTransaction

        offset = 0
        while True:
            q = (
                select(Model)
                .outerjoin(
                    Categorization,
                    (Categorization.target_id == Model.id)
                    & (Categorization.target_type == target_type.value),
                )
                .where(
                    (Categorization.id.is_(None))
                    | (Categorization.source != CategorizationSource.manual)
                )
                .order_by(Model.id)
                .limit(BATCH_SIZE)
                .offset(offset)
            )
            if transaction_ids is not None:
                q = q.where(Model.id.in_(transaction_ids))

            txs = (await session.scalars(q)).all()
            if not txs:
                break

            for tx in txs:
                for rule in applicable_rules:
                    if _matches(rule, tx):
                        cat_name = rule.category.name
                        counts[cat_name] += 1
                        total += 1

                        if not dry_run:
                            await _apply_categorization(session, tx, target_type, rule)
                        break  # first match wins

            if len(txs) < BATCH_SIZE:
                break
            offset += BATCH_SIZE

    return {
        "applied": total,
        "by_category": [
            {"category_name": name, "count": count}
            for name, count in sorted(counts.items(), key=lambda x: -x[1])
        ],
    }


async def _apply_categorization(
    session: AsyncSession,
    tx: BankTransaction | CreditCardTransaction,
    target_type: TargetType,
    rule: CategoryRule,
) -> None:
    existing = await session.scalar(
        select(Categorization).where(
            Categorization.target_id == tx.id,
            Categorization.target_type == target_type.value,
        )
    )

    now = datetime.now(tz=timezone.utc)

    if existing:
        action = EventAction.updated
        existing.category_id = rule.category_id
        existing.rule_id = rule.id
        existing.source = CategorizationSource.rule
        existing.confidence = None
        existing.updated_at = now
        cat_id = existing.id
    else:
        action = EventAction.created
        cat = Categorization(
            target_type=target_type,
            target_id=tx.id,
            category_id=rule.category_id,
            rule_id=rule.id,
            source=CategorizationSource.rule,
        )
        session.add(cat)
        await session.flush()
        cat_id = cat.id

    event = CategorizationEvent(
        id=uuid.uuid4(),
        categorization_id=cat_id,
        target_type=target_type.value,  # type: ignore[arg-type]
        target_id=tx.id,
        category_id=rule.category_id,
        rule_id=rule.id,
        action=action,
        source=CategorizationSource.rule,
    )
    session.add(event)
