"""add plaid v1 integration schema

Revision ID: 0003_plaid_v1_integration
Revises: 0002_nudge_decision_audit_fields
Create Date: 2026-04-25 23:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_plaid_v1_integration"
down_revision = "0002_nudge_decision_audit_fields"
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

    if "plaid_items" not in table_names:
        op.create_table(
            "plaid_items",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("plaid_item_id", sa.String(length=128), nullable=False),
            sa.Column("access_token", sa.String(length=255), nullable=False),
            sa.Column("institution_name", sa.String(length=120), nullable=True),
            sa.Column("sync_cursor", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'linked'")),
            sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_plaid_items_user_id_users"), ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_plaid_items")),
            sa.UniqueConstraint("plaid_item_id", name=op.f("uq_plaid_items_plaid_item_id")),
        )
    else:
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

        if "created_at" not in plaid_item_columns:
            op.add_column(
                "plaid_items",
                sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            )
        if "updated_at" not in plaid_item_columns:
            op.add_column(
                "plaid_items",
                sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
            )

    inspector = sa.inspect(bind)
    plaid_item_indexes = _index_names(inspector, "plaid_items")
    if "ix_plaid_items_plaid_item_id" not in plaid_item_indexes:
        op.create_index(op.f("ix_plaid_items_plaid_item_id"), "plaid_items", ["plaid_item_id"], unique=True)
    if "ix_plaid_items_user_id" not in plaid_item_indexes:
        op.create_index(op.f("ix_plaid_items_user_id"), "plaid_items", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plaid_items_user_id"), table_name="plaid_items")
    op.drop_index(op.f("ix_plaid_items_plaid_item_id"), table_name="plaid_items")
    op.drop_table("plaid_items")

    op.drop_constraint(op.f("uq_transactions_plaid_transaction_id"), "transactions", type_="unique")
    op.drop_index("ix_transactions_source", table_name="transactions")
    op.drop_column("transactions", "merchant_name")
    op.drop_column("transactions", "plaid_transaction_id")
    op.drop_column("transactions", "source")
