from __future__ import annotations

import datetime as dt
import json
import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models import Feedback, Goal, NudgeEvent, Transaction, User
from backend.services.nudge_models import (
    GoalContext,
    LastNudge,
    NudgeDecision,
    Prediction,
    RecentBehavior,
    RecentSpending,
    ResponsePattern,
    UserContext,
)

logger = logging.getLogger(__name__)
UTC = dt.timezone.utc


def _ensure_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _resolve_timezone_name(user: User) -> str:
    if user.timezone:
        try:
            ZoneInfo(user.timezone)
            return user.timezone
        except ZoneInfoNotFoundError:
            logger.warning("Invalid user timezone %s for user_id=%s", user.timezone, user.id)
    return "UTC"


def build_user_context(
    db: Session,
    user_id: int,
    category: str,
    now: dt.datetime | None = None,
) -> UserContext:
    current_time = _ensure_utc(now or dt.datetime.utcnow())
    user = db.execute(select(User).where(User.id == user_id)).scalar_one()
    timezone_name = _resolve_timezone_name(user)
    timezone = ZoneInfo(timezone_name)
    current_local = current_time.astimezone(timezone)

    transactions = db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.occurred_at.desc())
    ).scalars().all()
    category_transactions = [transaction for transaction in transactions if transaction.category == category]

    transactions_30d = [
        transaction
        for transaction in transactions
        if _ensure_utc(transaction.occurred_at) >= current_time - dt.timedelta(days=30)
    ]
    transactions_7d = [
        transaction
        for transaction in transactions_30d
        if _ensure_utc(transaction.occurred_at) >= current_time - dt.timedelta(days=7)
    ]
    category_transactions_30d = [
        transaction for transaction in transactions_30d if transaction.category == category
    ]
    category_transactions_7d = [
        transaction for transaction in transactions_7d if transaction.category == category
    ]

    category_amount_average_30d = None
    if category_transactions_30d:
        category_amount_average_30d = round(
            sum(float(transaction.amount) for transaction in category_transactions_30d)
            / len(category_transactions_30d),
            2,
        )

    last_category_transaction = category_transactions[0] if category_transactions else None
    days_since_last_purchase = None
    if last_category_transaction is not None:
        days_since_last_purchase = round(
            max(
                (_ensure_utc(last_category_transaction.occurred_at) - current_time).total_seconds() / -86400.0,
                0.0,
            ),
            2,
        )

    current_local_date = current_local.date()
    total_today = 0.0
    category_today = 0.0
    total_last_7d = 0.0
    category_last_7d = 0.0
    for transaction in transactions_7d:
        occurred_local = _ensure_utc(transaction.occurred_at).astimezone(timezone)
        amount = float(transaction.amount)
        total_last_7d += amount
        if transaction.category == category:
            category_last_7d += amount
        if occurred_local.date() == current_local_date:
            total_today += amount
            if transaction.category == category:
                category_today += amount

    active_goal = db.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.is_active.is_(True))
        .order_by(Goal.updated_at.desc(), Goal.id.desc())
    ).scalars().first()
    goal_context = None
    goal_remaining = None
    if active_goal is not None:
        goal_remaining = round(
            max(float(active_goal.target_amount) - float(active_goal.current_amount), 0.0),
            2,
        )
        goal_context = GoalContext(
            name=active_goal.name,
            target_amount=round(float(active_goal.target_amount), 2),
            current_amount=round(float(active_goal.current_amount), 2),
            remaining_amount=goal_remaining,
        )

    feedback_entries = db.execute(
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(Feedback.received_at.desc())
    ).scalars().all()
    feedback_entries = [
        entry
        for entry in feedback_entries
        if _ensure_utc(entry.received_at) >= current_time - dt.timedelta(days=30)
    ]
    positive_feedback_count = sum(1 for entry in feedback_entries if entry.response_type == "positive")
    negative_feedback_count = sum(1 for entry in feedback_entries if entry.response_type == "negative")

    recent_nudges = db.execute(
        select(NudgeEvent)
        .where(NudgeEvent.user_id == user_id)
        .order_by(NudgeEvent.sent_at.desc())
    ).scalars().all()
    recent_sent_nudges = recent_nudges[:5]
    last_nudges = [
        LastNudge(
            category=nudge.category,
            sent_at=_ensure_utc(nudge.sent_at),
            status=nudge.status,
            urgency=nudge.urgency,
            decision_source=nudge.decision_source,
        )
        for nudge in recent_sent_nudges[:3]
    ]

    ignored_recent_nudges = 0
    feedback_times = [_ensure_utc(entry.received_at) for entry in feedback_entries]
    for nudge in recent_sent_nudges:
        sent_at = _ensure_utc(nudge.sent_at)
        if sent_at < current_time - dt.timedelta(days=7):
            continue
        got_response = any(
            sent_at <= feedback_time <= sent_at + dt.timedelta(hours=24)
            for feedback_time in feedback_times
        )
        if not got_response:
            ignored_recent_nudges += 1

    recent_behavior = RecentBehavior(
        category_last_7d_count=len(category_transactions_7d),
        category_last_30d_count=len(category_transactions_30d),
        total_last_7d_count=len(transactions_7d),
        total_last_30d_count=len(transactions_30d),
        average_category_amount_30d=category_amount_average_30d,
        last_transaction_at=_ensure_utc(last_category_transaction.occurred_at)
        if last_category_transaction is not None
        else None,
        days_since_last_category_purchase=days_since_last_purchase,
    )
    response_pattern = ResponsePattern(
        feedback_count_30d=len(feedback_entries),
        positive_feedback_count_30d=positive_feedback_count,
        negative_feedback_count_30d=negative_feedback_count,
        ignored_recent_nudges=ignored_recent_nudges,
        last_feedback_at=_ensure_utc(feedback_entries[0].received_at) if feedback_entries else None,
    )
    recent_spending = RecentSpending(
        total_today=round(total_today, 2),
        category_today=round(category_today, 2),
        total_last_7d=round(total_last_7d, 2),
        category_last_7d=round(category_last_7d, 2),
    )
    return UserContext(
        goal=goal_context,
        goal_remaining=goal_remaining,
        recent_behavior=recent_behavior,
        response_pattern=response_pattern,
        recent_spending=recent_spending,
        last_nudges=last_nudges,
        timezone=timezone_name,
    )


def build_agent_prompt(prediction: Prediction, user_context: UserContext) -> str:
    settings = get_settings()
    prompt_payload = {
        "prediction_data": prediction.model_dump(mode="json"),
        "user_context": user_context.model_dump(mode="json"),
        "rules": {
            "role": "PiggyBank financial behavior assistant",
            "tone": ["conversational", "non-judgmental", "goal-oriented", "short"],
            "hard_constraints": [
                "Do not alter, invent, or reinterpret numeric prediction fields.",
                "Do not generate new probabilities, confidences, windows, or amounts.",
                "Reply with strict JSON only.",
                "Allowed urgency values: low, medium, high.",
                "Keep the SMS under 160 characters.",
                "If send is false, use an empty string for message.",
            ],
            "policy_hint": {
                "configured_probability_threshold": settings.prediction.nudge_probability_threshold,
                "ignored_recent_nudges_should_reduce_frequency": True,
                "goal_proximity_should_raise_urgency": True,
                "heavy_recent_spending_should_strengthen_intervention": True,
            },
            "required_json_schema": {
                "send": "boolean",
                "message": "string",
                "urgency": "low|medium|high",
                "reasoning": "string",
            },
        },
    }
    return (
        "You are Piggy, a financial behavior assistant. "
        "Interpret the structured inputs, decide whether to send a nudge, "
        "and produce JSON only.\n\n"
        f"{json.dumps(prompt_payload, ensure_ascii=True)}"
    )


def _strip_code_fences(raw_text: str) -> str:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()
    return cleaned


def _parse_gemini_response(raw_text: str) -> dict[str, object]:
    cleaned = _strip_code_fences(raw_text)
    return json.loads(cleaned)


def _call_gemini(prompt: str) -> dict[str, object]:
    settings = get_settings()
    if not settings.gemini.api_key:
        raise RuntimeError("Gemini API key is not configured.")

    import google.generativeai as genai

    genai.configure(api_key=settings.gemini.api_key)
    model = genai.GenerativeModel(settings.gemini.model)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
        request_options={"timeout": settings.gemini.timeout_seconds},
    )
    response_text = getattr(response, "text", None)
    if not response_text:
        raise RuntimeError("Gemini returned an empty response.")
    return _parse_gemini_response(response_text)


def _fallback_urgency(prediction: Prediction, user_context: UserContext) -> str:
    if user_context.goal_remaining is not None and user_context.goal_remaining <= 25:
        return "high"
    if user_context.recent_spending.total_today >= 30:
        return "high"
    if prediction.probability >= 0.8:
        return "medium"
    return "low"


def _build_fallback_message(
    prediction: Prediction,
    user_context: UserContext,
    urgency: str,
) -> str:
    category = prediction.category
    if user_context.goal is not None and user_context.goal_remaining is not None:
        return (
            f"You usually spend on {category} around now. "
            f"Skipping it today helps protect your progress toward {user_context.goal.name} "
            f"(${user_context.goal_remaining:.2f} left)."
        )[:160]
    if urgency == "high":
        return f"You are trending toward {category} soon. A lighter choice now could help keep today on track."[:160]
    return f"You are likely to buy {category} soon. Want to pause and make the cheaper option today?"[:160]


def _fallback_decision(
    prediction: Prediction,
    user_context: UserContext,
    reason: str,
) -> NudgeDecision:
    urgency = _fallback_urgency(prediction, user_context)
    return NudgeDecision(
        send=True,
        message=_build_fallback_message(prediction, user_context, urgency),
        urgency=urgency,  # type: ignore[arg-type]
        reasoning=reason,
        decision_source="fallback_rule",
    )


def decide_and_generate_nudge(
    prediction: Prediction,
    user_context: UserContext,
) -> NudgeDecision:
    prompt = build_agent_prompt(prediction, user_context)
    try:
        raw_payload = _call_gemini(prompt)
        decision = NudgeDecision(
            send=raw_payload["send"],
            message=raw_payload.get("message", ""),
            urgency=raw_payload["urgency"],
            reasoning=raw_payload["reasoning"],
            decision_source="gemini",
        )
        return decision
    except Exception as exc:
        logger.warning("Gemini decision failed, using fallback: %s", exc)
        return _fallback_decision(
            prediction=prediction,
            user_context=user_context,
            reason=f"Fallback rule used because Gemini failed: {exc.__class__.__name__}",
        )
