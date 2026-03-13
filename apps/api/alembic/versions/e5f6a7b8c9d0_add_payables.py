"""Add payables and recurring patterns.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-13 00:00:00.000000
"""
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE recurringcadence AS ENUM ('monthly', 'weekly', 'yearly', 'custom')")
    op.execute("CREATE TYPE detectionsource AS ENUM ('system', 'manual')")
    op.execute("CREATE TYPE recurringpatternstatus AS ENUM ('suggested', 'approved', 'ignored')")
    op.execute("CREATE TYPE payablesourcetype AS ENUM ('manual', 'recurring_pattern')")
    op.execute("CREATE TYPE occurrencestatus AS ENUM ('expected', 'pending', 'paid', 'ignored')")

    op.execute("""
        CREATE TABLE recurring_patterns (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            normalized_description TEXT NOT NULL UNIQUE,
            category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
            expected_amount_minor BIGINT,
            cadence recurringcadence NOT NULL DEFAULT 'monthly',
            detection_source detectionsource NOT NULL DEFAULT 'system',
            status recurringpatternstatus NOT NULL DEFAULT 'suggested',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE payables (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
            default_amount_minor BIGINT,
            notes TEXT,
            source_type payablesourcetype NOT NULL DEFAULT 'manual',
            recurring_pattern_id UUID REFERENCES recurring_patterns(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE payable_occurrences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            payable_id UUID NOT NULL REFERENCES payables(id) ON DELETE CASCADE,
            due_date DATE NOT NULL,
            expected_amount_minor BIGINT NOT NULL DEFAULT 0,
            actual_amount_minor BIGINT,
            status occurrencestatus NOT NULL DEFAULT 'expected',
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS payable_occurrences")
    op.execute("DROP TABLE IF EXISTS payables")
    op.execute("DROP TABLE IF EXISTS recurring_patterns")
    op.execute("DROP TYPE IF EXISTS occurrencestatus")
    op.execute("DROP TYPE IF EXISTS payablesourcetype")
    op.execute("DROP TYPE IF EXISTS recurringpatternstatus")
    op.execute("DROP TYPE IF EXISTS detectionsource")
    op.execute("DROP TYPE IF EXISTS recurringcadence")
