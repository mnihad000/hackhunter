from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class NudgeEvent(Base):
    __tablename__ = "nudge_events"
    __table_args__ = (
        Index("ix_nudge_events_user_sent_at", "user_id", "sent_at"),
        Index("ix_nudge_events_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    predicted_probability: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    scheduled_for: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=dt.datetime.utcnow,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    message_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_message_sid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_source: Mapped[str | None] = mapped_column(String(32), nullable=True)

    user = relationship("User", back_populates="nudge_events")
