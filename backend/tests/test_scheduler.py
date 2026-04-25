from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.session import get_engine
from backend.models import Goal, NudgeEvent, Transaction, User
from backend.services import agent
from backend.services.scheduler import run_nudge_cycle


def _db_session() -> Session:
    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    return Session(engine)


def test_run_nudge_cycle_persists_sent_nudge_with_decision_fields(monkeypatch):
    now = dt.datetime(2026, 4, 24, 21, 25, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(
        agent,
        "_call_gemini",
        lambda prompt: {
            "send": True,
            "message": "You usually grab food after work. Want to eat at home today?",
            "urgency": "high",
            "reasoning": "Strong routine, goal is close, and spending is elevated today.",
        },
    )

    with _db_session() as db:
        user = User(phone_number="+15553330001", timezone="America/New_York")
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(
            Goal(
                user_id=user.id,
                name="Bike",
                target_amount=Decimal("250.00"),
                current_amount=Decimal("225.00"),
                is_active=True,
            )
        )
        for occurred_at in [
            dt.datetime(2026, 4, 20, 21, 30),
            dt.datetime(2026, 4, 21, 21, 30),
            dt.datetime(2026, 4, 22, 21, 30),
            dt.datetime(2026, 4, 23, 21, 30),
        ]:
            db.add(
                Transaction(
                    user_id=user.id,
                    category="food",
                    amount=Decimal("14.00"),
                    occurred_at=occurred_at,
                )
            )
        db.commit()

        events = run_nudge_cycle(db, now=now)

        assert len(events) == 1
        event = events[0]
        assert event.status == "sent"
        assert event.urgency == "high"
        assert event.decision_source == "gemini"
        assert "Strong routine" in event.decision_reason

        stored_events = db.execute(select(NudgeEvent)).scalars().all()

    assert len(stored_events) == 1
    assert stored_events[0].provider_message_sid == "test-message-sid"
    assert "eat at home" in stored_events[0].message_body
