"""add plaid items and transaction source fields

Revision ID: 0003_plaid
Revises: 0002_nudge_decision_audit_fields
Create Date: 2026-04-25 18:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_plaid"
down_revision = "0002_nudge_decision_audit_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plaid_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plaid_item_id", sa.String(length=128), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("institution_id", sa.String(length=128), nullable=True),
        sa.Column("institution_name", sa.String(length=255), nullable=True),
        sa.Column("sync_cursor", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_plaid_items_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plaid_items")),
        sa.UniqueConstraint("plaid_item_id", name=op.f("uq_plaid_items_plaid_item_id")),
    )
    op.create_index(op.f("ix_plaid_items_plaid_item_id"), "plaid_items", ["plaid_item_id"], unique=True)
    op.create_index(op.f("ix_plaid_items_user_id"), "plaid_items", ["user_id"], unique=False)

    op.add_column("transactions", sa.Column("merchant_name", sa.String(length=255), nullable=True))
    op.add_column(
        "transactions",
        sa.Column("source", sa.String(length=32), nullable=False, server_default=sa.text("'sms'")),
    )
    op.add_column("transactions", sa.Column("external_id", sa.String(length=128), nullable=True))
    op.add_column(
        "transactions",
        sa.Column("pending", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_unique_constraint(
        "uq_transactions_source_external_id",
        "transactions",
        ["source", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_transactions_source_external_id", "transactions", type_="unique")
    op.drop_column("transactions", "pending")
    op.drop_column("transactions", "external_id")
    op.drop_column("transactions", "source")
    op.drop_column("transactions", "merchant_name")

    op.drop_index(op.f("ix_plaid_items_user_id"), table_name="plaid_items")
    op.drop_index(op.f("ix_plaid_items_plaid_item_id"), table_name="plaid_items")
    op.drop_table("plaid_items")
