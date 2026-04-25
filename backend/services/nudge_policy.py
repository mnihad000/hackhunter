from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models import NudgeEvent, Transaction
from backend.services.nudge_models import PolicyDecision, Prediction, UserContext

UTC = dt.timezone.utc


def _ensure_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def evaluate_nudge_eligibility(
    db: Session,
    user_id: int,
    prediction: Prediction,
    user_context: UserContext,
    now: dt.datetime | None = None,
) -> PolicyDecision:
    settings = get_settings()
    current_time = _ensure_utc(now or dt.datetime.utcnow())
    base_cooldown = settings.prediction.nudge_cooldown_minutes
    fatigue_extension = user_context.response_pattern.ignored_recent_nudges * 30
    effective_cooldown = base_cooldown + fatigue_extension
    reasons: list[str] = []

    if prediction.probability < settings.prediction.nudge_probability_threshold:
        return PolicyDecision(
            eligible=False,
            reason_codes=["below_probability_threshold"],
            blocked_by="probability_threshold",
            effective_cooldown_minutes=effective_cooldown,
        )

    if current_time < prediction.window_start or current_time > prediction.window_end:
        return PolicyDecision(
            eligible=False,
            reason_codes=["outside_prediction_window"],
            blocked_by="prediction_window",
            effective_cooldown_minutes=effective_cooldown,
        )

    recent_nudge = db.execute(
        select(NudgeEvent)
        .where(NudgeEvent.user_id == user_id, NudgeEvent.status == "sent")
        .order_by(NudgeEvent.sent_at.desc())
    ).scalars().first()
    if recent_nudge is not None:
        last_sent_at = _ensure_utc(recent_nudge.sent_at)
        if current_time < last_sent_at + dt.timedelta(minutes=effective_cooldown):
            return PolicyDecision(
                eligible=False,
                reason_codes=["nudge_cooldown_active"],
                blocked_by="cooldown",
                effective_cooldown_minutes=effective_cooldown,
            )

    recent_same_category_transaction = db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.category == prediction.category,
        )
        .order_by(Transaction.occurred_at.desc())
    ).scalars().all()
    recent_same_category_transaction = next(
        (
            transaction
            for transaction in recent_same_category_transaction
            if _ensure_utc(transaction.occurred_at) >= prediction.window_start
        ),
        None,
    )
    if recent_same_category_transaction is not None:
        return PolicyDecision(
            eligible=False,
            reason_codes=["already_purchased_in_active_window"],
            blocked_by="recent_purchase",
            effective_cooldown_minutes=effective_cooldown,
        )

    if user_context.response_pattern.ignored_recent_nudges > 0:
        reasons.append("fatigue_adjusted_cooldown")
    reasons.append("eligible_for_gemini_review")
    return PolicyDecision(
        eligible=True,
        reason_codes=reasons,
        blocked_by=None,
        effective_cooldown_minutes=effective_cooldown,
    )
