from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base, TimestampMixin


class Goal(TimestampMixin, Base):
    __tablename__ = "goals"
    __table_args__ = (
        Index("ix_goals_user_active", "user_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    current_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="goals")
