from __future__ import annotations

import datetime as dt
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import NudgeEvent, Transaction, User
from backend.services.twilio_sender import send_sms

RAPID_REPEAT_WINDOW_MINUTES = 5
RAPID_REPEAT_TRIGGER_COUNT = 3
RAPID_REPEAT_DECISION_SOURCE = "rapid_repeat_demo"


def _build_demo_message(category: str, total_today: Decimal) -> str:
    category_name = category.strip().lower() or "this category"
    message = (
        f"You have spent ${total_today:.2f} on {category_name} around this time. "
        f"Maybe consider not spending on {category_name} today?"
    )
    if len(message) <= 160:
        return message

    fallback = (
        f"You have spent ${total_today:.2f} on {category_name} today. "
        f"Maybe skip {category_name} this time?"
    )
    return fallback[:160]


def maybe_send_rapid_repeat_demo_nudge(
    db: Session,
    user: User,
    category: str,
    latest_occurred_at: dt.datetime,
) -> NudgeEvent | None:
    window_start = latest_occurred_at - dt.timedelta(minutes=RAPID_REPEAT_WINDOW_MINUTES)

    rapid_repeat_count = db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == user.id,
            Transaction.category == category,
            Transaction.source == "sms",
            Transaction.occurred_at >= window_start,
            Transaction.occurred_at <= latest_occurred_at,
        )
    ).scalar_one()
    if rapid_repeat_count < RAPID_REPEAT_TRIGGER_COUNT:
        return None

    existing_demo_event = db.execute(
        select(NudgeEvent)
        .where(
            NudgeEvent.user_id == user.id,
            NudgeEvent.category == category,
            NudgeEvent.decision_source == RAPID_REPEAT_DECISION_SOURCE,
            NudgeEvent.sent_at >= window_start,
            NudgeEvent.sent_at <= latest_occurred_at,
        )
        .order_by(NudgeEvent.sent_at.desc())
    ).scalars().first()
    if existing_demo_event is not None:
        return None

    day_start = latest_occurred_at.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + dt.timedelta(days=1)
    total_today_raw = db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.category == category,
            Transaction.occurred_at >= day_start,
            Transaction.occurred_at < day_end,
        )
    ).scalar_one()
    total_today = Decimal(str(total_today_raw or 0)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    message = _build_demo_message(category, total_today)

    provider_result = send_sms(user.phone_number, message)
    event = NudgeEvent(
        user_id=user.id,
        category=category,
        predicted_probability=None,
        confidence=None,
        scheduled_for=latest_occurred_at,
        sent_at=latest_occurred_at,
        status="sent" if provider_result.success else provider_result.status,
        message_body=message,
        provider_message_sid=provider_result.provider_message_sid,
        urgency="medium",
        decision_reason=f"rapid_repeat_{category}_within_{RAPID_REPEAT_WINDOW_MINUTES}m",
        decision_source=RAPID_REPEAT_DECISION_SOURCE,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
