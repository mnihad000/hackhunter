"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-25 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("phone_number", name=op.f("uq_users_phone_number")),
    )
    op.create_index(op.f("ix_users_phone_number"), "users", ["phone_number"], unique=True)

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("response_type", sa.String(length=32), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_feedback_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback")),
    )
    op.create_index(op.f("ix_feedback_user_id"), "feedback", ["user_id"], unique=False)
    op.create_index("ix_feedback_user_received_at", "feedback", ["user_id", "received_at"], unique=False)

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("target_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("current_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_goals_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_goals")),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"], unique=False)
    op.create_index("ix_goals_user_active", "goals", ["user_id", "is_active"], unique=False)

    op.create_table(
        "nudge_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("predicted_probability", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("message_body", sa.Text(), nullable=True),
        sa.Column("provider_message_sid", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_nudge_events_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_nudge_events")),
    )
    op.create_index(op.f("ix_nudge_events_user_id"), "nudge_events", ["user_id"], unique=False)
    op.create_index("ix_nudge_events_status", "nudge_events", ["status"], unique=False)
    op.create_index("ix_nudge_events_user_sent_at", "nudge_events", ["user_id", "sent_at"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_transactions_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(op.f("ix_transactions_category"), "transactions", ["category"], unique=False)
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_index("ix_transactions_user_occurred_at", "transactions", ["user_id", "occurred_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_transactions_user_occurred_at", table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category"), table_name="transactions")
    op.drop_table("transactions")

    op.drop_index("ix_nudge_events_user_sent_at", table_name="nudge_events")
    op.drop_index("ix_nudge_events_status", table_name="nudge_events")
    op.drop_index(op.f("ix_nudge_events_user_id"), table_name="nudge_events")
    op.drop_table("nudge_events")

    op.drop_index("ix_goals_user_active", table_name="goals")
    op.drop_index(op.f("ix_goals_user_id"), table_name="goals")
    op.drop_table("goals")

    op.drop_index("ix_feedback_user_received_at", table_name="feedback")
    op.drop_index(op.f("ix_feedback_user_id"), table_name="feedback")
    op.drop_table("feedback")

    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_table("users")
