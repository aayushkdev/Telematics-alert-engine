"""Widen rule operator column.

Revision ID: c5e6f7a8b9c0
Revises: b4d1e2f3a4b5
Create Date: 2026-08-11
"""

from alembic import op
import sqlalchemy as sa


revision = "c5e6f7a8b9c0"
down_revision = "b4d1e2f3a4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "rules",
        "operator",
        existing_type=sa.String(length=10),
        type_=sa.String(length=32),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "rules",
        "operator",
        existing_type=sa.String(length=32),
        type_=sa.String(length=10),
        existing_nullable=False,
    )
