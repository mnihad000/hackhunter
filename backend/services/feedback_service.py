from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from backend.models import Feedback

POSITIVE_FEEDBACK = {"yes", "y", "ok", "okay"}
NEGATIVE_FEEDBACK = {"no", "n", "nah", "skip"}
NEUTRAL_FEEDBACK = {"maybe"}


def normalize_feedback_type(message: str) -> str | None:
    normalized = message.strip().lower()
    if not normalized:
        return None
    if normalized in POSITIVE_FEEDBACK:
        return "positive"
    if normalized in NEGATIVE_FEEDBACK:
        return "negative"
    if normalized in NEUTRAL_FEEDBACK:
        return "neutral"
    return "other"


def save_feedback(
    db: Session,
    user_id: int,
    message: str,
    received_at: dt.datetime | None = None,
) -> Feedback:
    feedback = Feedback(
        user_id=user_id,
        message=message.strip(),
        response_type=normalize_feedback_type(message),
        processed=False,
        received_at=received_at or dt.datetime.utcnow(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
