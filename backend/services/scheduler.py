from __future__ import annotations

import asyncio
import datetime as dt
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import Environment, get_settings
from backend.db.session import get_session_factory
from backend.models import NudgeEvent, User
from backend.services.agent import build_user_context, decide_and_generate_nudge
from backend.services.nudge_models import NudgeDecision, Prediction, ProviderResult
from backend.services.nudge_policy import evaluate_nudge_eligibility
from backend.services.prediction import predict_for_user
from backend.services.twilio_sender import send_sms

logger = logging.getLogger(__name__)
UTC = dt.timezone.utc


def _ensure_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _persist_nudge_event(
    db: Session,
    user_id: int,
    prediction: Prediction,
    decision: NudgeDecision,
    provider_result: ProviderResult,
    sent_at: dt.datetime,
) -> NudgeEvent:
    event = NudgeEvent(
        user_id=user_id,
        category=prediction.category,
        predicted_probability=prediction.probability,
        confidence=prediction.confidence,
        scheduled_for=prediction.predicted_at,
        sent_at=sent_at,
        status="sent" if provider_result.success else provider_result.status,
        message_body=decision.message,
        provider_message_sid=provider_result.provider_message_sid,
        urgency=decision.urgency,
        decision_reason=decision.reasoning,
        decision_source=decision.decision_source,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def process_user_nudges(
    db: Session,
    user_id: int,
    now: dt.datetime | None = None,
) -> NudgeEvent | None:
    settings = get_settings()
    current_time = _ensure_utc(now or dt.datetime.utcnow())
    user = db.execute(select(User).where(User.id == user_id, User.is_active.is_(True))).scalar_one_or_none()
    if user is None:
        return None

    predictions = predict_for_user(db, user_id=user_id, now=current_time)
    if not predictions:
        return None

    max_candidates = settings.prediction.max_candidates_per_user
    eligible_candidates: list[tuple[Prediction, object]] = []
    for prediction in predictions:
        user_context = build_user_context(db, user_id=user_id, category=prediction.category, now=current_time)
        policy_decision = evaluate_nudge_eligibility(
            db,
            user_id=user_id,
            prediction=prediction,
            user_context=user_context,
            now=current_time,
        )
        if policy_decision.eligible:
            eligible_candidates.append((prediction, user_context))

    if not eligible_candidates:
        return None

    eligible_candidates.sort(
        key=lambda item: (item[0].probability, item[0].confidence, item[0].predicted_at),
        reverse=True,
    )
    prediction, user_context = eligible_candidates[:max_candidates][0]
    decision = decide_and_generate_nudge(prediction, user_context)
    if not decision.send or not decision.message.strip():
        logger.info(
            "Skipping nudge after decision layer for user_id=%s category=%s source=%s",
            user_id,
            prediction.category,
            decision.decision_source,
        )
        return None

    provider_result = send_sms(user.phone_number, decision.message)
    return _persist_nudge_event(
        db=db,
        user_id=user_id,
        prediction=prediction,
        decision=decision,
        provider_result=provider_result,
        sent_at=current_time,
    )


def run_nudge_cycle(
    db: Session,
    now: dt.datetime | None = None,
) -> list[NudgeEvent]:
    current_time = _ensure_utc(now or dt.datetime.utcnow())
    user_ids = db.execute(
        select(User.id).where(User.is_active.is_(True)).order_by(User.id.asc())
    ).scalars().all()
    sent_events: list[NudgeEvent] = []
    for user_id in user_ids:
        event = process_user_nudges(db, user_id=user_id, now=current_time)
        if event is not None:
            sent_events.append(event)
    return sent_events


async def run_scheduler_forever() -> None:
    settings = get_settings()
    if not settings.database.url:
        logger.warning("Scheduler not started because DATABASE__URL is missing.")
        return

    session_factory = get_session_factory(settings.database.url, settings.database.echo)
    logger.info("Starting nudge scheduler loop with %s second interval.", settings.scheduler.interval_seconds)
    while True:
        try:
            with session_factory() as db:
                run_nudge_cycle(db)
        except Exception:
            logger.exception("Scheduler cycle failed.")
        await asyncio.sleep(settings.scheduler.interval_seconds)


def should_start_scheduler() -> bool:
    settings = get_settings()
    return settings.scheduler.enabled and settings.app.env != Environment.test
