"""Add geofence fields to rules.

Revision ID: b4d1e2f3a4b5
Revises: 9c8f4f3c2b1a
Create Date: 2026-08-11
"""

from alembic import op
import sqlalchemy as sa


revision = "b4d1e2f3a4b5"
down_revision = "9c8f4f3c2b1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rules", sa.Column("center_latitude", sa.Float(), nullable=True))
    op.add_column("rules", sa.Column("center_longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("rules", "center_longitude")
    op.drop_column("rules", "center_latitude")
