"""Add investments tables.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-13 00:00:00.000000
"""
from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE assetclass AS ENUM ('stock', 'bond', 'etf', 'real_estate', 'crypto', 'cash', 'other')")

    op.execute("""
        CREATE TABLE investment_accounts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            institution_name TEXT,
            currency CHAR(3) NOT NULL DEFAULT 'BRL',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            symbol VARCHAR(20),
            name TEXT NOT NULL,
            asset_class assetclass NOT NULL,
            currency CHAR(3) NOT NULL DEFAULT 'BRL',
            metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE asset_positions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            investment_account_id UUID NOT NULL REFERENCES investment_accounts(id) ON DELETE CASCADE,
            asset_id UUID NOT NULL REFERENCES assets(id),
            quantity FLOAT NOT NULL DEFAULT 0,
            average_cost_minor BIGINT,
            current_value_minor BIGINT,
            as_of_date DATE NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE portfolio_snapshots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            snapshot_date DATE NOT NULL,
            total_value_minor BIGINT NOT NULL DEFAULT 0,
            currency CHAR(3) NOT NULL DEFAULT 'BRL',
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS portfolio_snapshots")
    op.execute("DROP TABLE IF EXISTS asset_positions")
    op.execute("DROP TABLE IF EXISTS assets")
    op.execute("DROP TABLE IF EXISTS investment_accounts")
    op.execute("DROP TYPE IF EXISTS assetclass")
