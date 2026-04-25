"""add nudge decision audit fields

Revision ID: 0002_nudge_decision_audit_fields
Revises: 0001_initial_schema
Create Date: 2026-04-25 00:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_nudge_decision_audit_fields"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("nudge_events", sa.Column("urgency", sa.String(length=16), nullable=True))
    op.add_column("nudge_events", sa.Column("decision_reason", sa.Text(), nullable=True))
    op.add_column("nudge_events", sa.Column("decision_source", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("nudge_events", "decision_source")
    op.drop_column("nudge_events", "decision_reason")
    op.drop_column("nudge_events", "urgency")
