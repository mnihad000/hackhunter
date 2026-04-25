from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.session import get_engine
from backend.models import NudgeEvent, Transaction, User
from backend.services.nudge_models import Prediction, RecentBehavior, RecentSpending, ResponsePattern, UserContext
from backend.services.nudge_policy import evaluate_nudge_eligibility


def _db_session() -> Session:
    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    return Session(engine)


def _prediction(now: dt.datetime, probability: float = 0.8) -> Prediction:
    return Prediction(
        category="food",
        predicted_at=now,
        window_start=now - dt.timedelta(minutes=20),
        window_end=now + dt.timedelta(minutes=20),
        probability=probability,
        confidence=0.82,
        support_count=4,
        reason_codes=["consistent_interval"],
    )


def _context(ignored_recent_nudges: int = 0) -> UserContext:
    return UserContext(
        recent_behavior=RecentBehavior(),
        response_pattern=ResponsePattern(ignored_recent_nudges=ignored_recent_nudges),
        recent_spending=RecentSpending(),
        last_nudges=[],
        timezone="UTC",
    )


def test_policy_blocks_below_threshold_prediction():
    now = dt.datetime(2026, 4, 25, 18, 0, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15551110001")
        db.add(user)
        db.commit()
        db.refresh(user)

        decision = evaluate_nudge_eligibility(
            db,
            user_id=user.id,
            prediction=_prediction(now, probability=0.4),
            user_context=_context(),
            now=now,
        )

    assert decision.eligible is False
    assert decision.blocked_by == "probability_threshold"


def test_policy_blocks_when_cooldown_is_active():
    now = dt.datetime(2026, 4, 25, 18, 0, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15551110002")
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(
            NudgeEvent(
                user_id=user.id,
                category="food",
                predicted_probability=Decimal("0.8000"),
                confidence=Decimal("0.7000"),
                scheduled_for=now - dt.timedelta(minutes=5),
                sent_at=now - dt.timedelta(minutes=10),
                status="sent",
                message_body="Previous nudge",
            )
        )
        db.commit()

        decision = evaluate_nudge_eligibility(
            db,
            user_id=user.id,
            prediction=_prediction(now),
            user_context=_context(ignored_recent_nudges=1),
            now=now,
        )

    assert decision.eligible is False
    assert decision.blocked_by == "cooldown"
    assert decision.effective_cooldown_minutes > 120


def test_policy_blocks_if_user_already_purchased_same_category_in_window():
    now = dt.datetime(2026, 4, 25, 18, 0, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15551110003")
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(
            Transaction(
                user_id=user.id,
                category="food",
                amount=Decimal("15.00"),
                occurred_at=(now - dt.timedelta(minutes=5)).replace(tzinfo=None),
            )
        )
        db.commit()

        decision = evaluate_nudge_eligibility(
            db,
            user_id=user.id,
            prediction=_prediction(now),
            user_context=_context(),
            now=now,
        )

    assert decision.eligible is False
    assert decision.blocked_by == "recent_purchase"


def test_policy_allows_eligible_prediction():
    now = dt.datetime(2026, 4, 25, 18, 0, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15551110004")
        db.add(user)
        db.commit()
        db.refresh(user)

        decision = evaluate_nudge_eligibility(
            db,
            user_id=user.id,
            prediction=_prediction(now),
            user_context=_context(),
            now=now,
        )

    assert decision.eligible is True
    assert decision.blocked_by is None
    assert "eligible_for_gemini_review" in decision.reason_codes
