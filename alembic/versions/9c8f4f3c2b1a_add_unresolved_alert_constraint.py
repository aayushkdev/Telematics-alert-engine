"""Add unresolved alert uniqueness constraint.

Revision ID: 9c8f4f3c2b1a
Revises: 5e234734ed81
Create Date: 2026-08-11
"""

from alembic import op
import sqlalchemy as sa


revision = "9c8f4f3c2b1a"
down_revision = "5e234734ed81"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_alerts_unresolved_rule_vehicle",
        "alerts",
        ["rule_id", "vehicle_id"],
        unique=True,
        postgresql_where=sa.text("status != 'RESOLVED'"),
    )


def downgrade() -> None:
    op.drop_index("uq_alerts_unresolved_rule_vehicle", table_name="alerts")
