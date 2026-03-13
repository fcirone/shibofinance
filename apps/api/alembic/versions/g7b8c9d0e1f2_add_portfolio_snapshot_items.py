"""Add portfolio_snapshot_items and unique constraint on portfolio_snapshots.

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-13 00:00:00.000000
"""
from alembic import op

revision = "g7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE portfolio_snapshots
        ADD CONSTRAINT portfolio_snapshots_snapshot_date_key UNIQUE (snapshot_date)
    """)

    op.execute("""
        CREATE TABLE portfolio_snapshot_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            snapshot_id UUID NOT NULL REFERENCES portfolio_snapshots(id) ON DELETE CASCADE,
            asset_id UUID NOT NULL REFERENCES assets(id),
            investment_account_id UUID NOT NULL REFERENCES investment_accounts(id),
            asset_name TEXT NOT NULL,
            asset_symbol VARCHAR(20),
            asset_class assetclass NOT NULL,
            quantity FLOAT NOT NULL DEFAULT 0,
            current_value_minor BIGINT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE INDEX idx_portfolio_snapshot_items_snapshot_id
        ON portfolio_snapshot_items (snapshot_id)
    """)

    op.execute("""
        CREATE INDEX idx_portfolio_snapshot_items_asset_id
        ON portfolio_snapshot_items (asset_id)
    """)

    op.execute("""
        CREATE INDEX idx_portfolio_snapshots_snapshot_date
        ON portfolio_snapshots (snapshot_date)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS portfolio_snapshot_items")
    op.execute("ALTER TABLE portfolio_snapshots DROP CONSTRAINT IF EXISTS portfolio_snapshots_snapshot_date_key")
    op.execute("DROP INDEX IF EXISTS idx_portfolio_snapshot_items_snapshot_id")
    op.execute("DROP INDEX IF EXISTS idx_portfolio_snapshot_items_asset_id")
    op.execute("DROP INDEX IF EXISTS idx_portfolio_snapshots_snapshot_date")
