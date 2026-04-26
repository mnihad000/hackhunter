"""repair partial plaid schema installations

Revision ID: 0004_plaid_schema_compatibility
Revises: 0003_plaid_v1_integration
Create Date: 2026-04-26 00:25:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_plaid_schema_compatibility"
down_revision = "0003_plaid_v1_integration"
branch_labels = None
depends_on = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _has_unique_shape(inspector: sa.Inspector, table_name: str, columns: tuple[str, ...]) -> bool:
    expected = set(columns)
    for constraint in inspector.get_unique_constraints(table_name):
        if set(constraint.get("column_names") or []) == expected:
            return True
    for index in inspector.get_indexes(table_name):
        if index.get("unique") and set(index.get("column_names") or []) == expected:
            return True
    return False


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "transactions" in table_names:
        transaction_columns = _column_names(inspector, "transactions")
        if "source" not in transaction_columns:
            op.add_column(
                "transactions",
                sa.Column("source", sa.String(length=16), nullable=True, server_default=sa.text("'sms'")),
            )
            bind.execute(sa.text("UPDATE transactions SET source = 'sms' WHERE source IS NULL"))
        else:
            bind.execute(sa.text("UPDATE transactions SET source = 'sms' WHERE source IS NULL"))

        if "plaid_transaction_id" not in transaction_columns:
            op.add_column("transactions", sa.Column("plaid_transaction_id", sa.String(length=128), nullable=True))

        if "merchant_name" not in transaction_columns:
            op.add_column("transactions", sa.Column("merchant_name", sa.String(length=120), nullable=True))

        inspector = sa.inspect(bind)
        transaction_indexes = _index_names(inspector, "transactions")
        if "ix_transactions_source" not in transaction_indexes:
            op.create_index("ix_transactions_source", "transactions", ["source"], unique=False)

        if not _has_unique_shape(inspector, "transactions", ("plaid_transaction_id",)):
            op.create_index(
                "ix_transactions_plaid_transaction_id_unique",
                "transactions",
                ["plaid_transaction_id"],
                unique=True,
            )

    if "plaid_items" in table_names:
        plaid_item_columns = _column_names(inspector, "plaid_items")
        if "status" not in plaid_item_columns:
            op.add_column(
                "plaid_items",
                sa.Column("status", sa.String(length=32), nullable=True, server_default=sa.text("'linked'")),
            )
            bind.execute(sa.text("UPDATE plaid_items SET status = 'linked' WHERE status IS NULL"))
        else:
            bind.execute(sa.text("UPDATE plaid_items SET status = 'linked' WHERE status IS NULL"))

        if "last_synced_at" not in plaid_item_columns:
            op.add_column("plaid_items", sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True))

        inspector = sa.inspect(bind)
        plaid_item_indexes = _index_names(inspector, "plaid_items")
        if "ix_plaid_items_user_id" not in plaid_item_indexes:
            op.create_index("ix_plaid_items_user_id", "plaid_items", ["user_id"], unique=False)
        if "ix_plaid_items_plaid_item_id" not in plaid_item_indexes:
            op.create_index("ix_plaid_items_plaid_item_id", "plaid_items", ["plaid_item_id"], unique=True)


def downgrade() -> None:
    # This migration repairs partial live schemas in place. Downgrading it safely is not
    # well-defined because we cannot distinguish newly added fields from preexisting manual state.
    pass
