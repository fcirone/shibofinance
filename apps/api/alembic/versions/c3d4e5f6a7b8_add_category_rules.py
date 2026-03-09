"""add category rules and categorization events

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-03-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE matchfield AS ENUM ('description_raw', 'description_norm', 'merchant_raw', 'amount_minor')")
    op.execute("CREATE TYPE matchoperator AS ENUM ('contains', 'equals', 'regex', 'gte', 'lte')")
    op.execute("CREATE TYPE ruletargettype AS ENUM ('bank_transaction', 'card_transaction', 'both')")
    op.execute("CREATE TYPE eventaction AS ENUM ('created', 'updated', 'deleted')")

    op.execute("""
        CREATE TABLE category_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            category_id UUID NOT NULL REFERENCES categories(id),
            match_field matchfield NOT NULL,
            match_operator matchoperator NOT NULL,
            match_value TEXT NOT NULL,
            target_type ruletargettype NOT NULL,
            priority INTEGER NOT NULL DEFAULT 100,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE categorization_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            categorization_id UUID,
            target_type ruletargettype NOT NULL,
            target_id UUID NOT NULL,
            category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
            rule_id UUID,
            action eventaction NOT NULL,
            source categorizationsource NOT NULL,
            confidence FLOAT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        ALTER TABLE categorizations
        ADD CONSTRAINT fk_categorizations_rule_id
        FOREIGN KEY (rule_id) REFERENCES category_rules(id) ON DELETE SET NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE categorizations DROP CONSTRAINT IF EXISTS fk_categorizations_rule_id")
    op.execute("DROP TABLE IF EXISTS categorization_events")
    op.execute("DROP TABLE IF EXISTS category_rules")
    op.execute("DROP TYPE IF EXISTS eventaction")
    op.execute("DROP TYPE IF EXISTS ruletargettype")
    op.execute("DROP TYPE IF EXISTS matchoperator")
    op.execute("DROP TYPE IF EXISTS matchfield")
