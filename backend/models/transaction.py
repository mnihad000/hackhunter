from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_occurred_at", "user_id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=dt.datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="transactions")
