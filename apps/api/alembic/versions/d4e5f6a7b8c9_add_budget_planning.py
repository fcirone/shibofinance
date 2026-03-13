"""add budget planning tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE budgetperiodstatus AS ENUM ('open', 'closed')")

    op.execute("""
        CREATE TABLE budget_periods (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            year INTEGER NOT NULL,
            month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
            status budgetperiodstatus NOT NULL DEFAULT 'open',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (year, month)
        )
    """)

    op.execute("""
        CREATE TABLE category_budgets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            budget_period_id UUID NOT NULL REFERENCES budget_periods(id) ON DELETE CASCADE,
            category_id UUID NOT NULL REFERENCES categories(id),
            planned_amount_minor BIGINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (budget_period_id, category_id)
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS category_budgets")
    op.execute("DROP TABLE IF EXISTS budget_periods")
    op.execute("DROP TYPE IF EXISTS budgetperiodstatus")
