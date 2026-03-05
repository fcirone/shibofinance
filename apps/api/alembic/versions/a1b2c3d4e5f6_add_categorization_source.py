"""add categorization source

Revision ID: a1b2c3d4e5f6
Revises: 2412e25c519e
Create Date: 2026-03-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2412e25c519e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE categorizationsource AS ENUM ('manual', 'rule', 'system')")
    op.add_column(
        'categorizations',
        sa.Column(
            'source',
            sa.Enum('manual', 'rule', 'system', name='categorizationsource'),
            nullable=True,
        ),
    )
    op.execute("UPDATE categorizations SET source = 'system' WHERE source IS NULL")
    op.alter_column('categorizations', 'source', nullable=False, server_default='manual')


def downgrade() -> None:
    op.drop_column('categorizations', 'source')
    op.execute("DROP TYPE categorizationsource")
