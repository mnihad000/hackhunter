from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models import Transaction, User
from backend.services.nudge_models import Prediction

UTC = dt.timezone.utc


def _ensure_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _resolve_timezone(user: User) -> tuple[ZoneInfo, str]:
    if user.timezone:
        try:
            return ZoneInfo(user.timezone), user.timezone
        except ZoneInfoNotFoundError:
            pass
    return ZoneInfo("UTC"), "UTC"


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _weighted_mean(values: list[float], weights: list[float]) -> float:
    weight_total = sum(weights)
    if not values or weight_total <= 0:
        return 0.0
    return sum(value * weight for value, weight in zip(values, weights, strict=True)) / weight_total


def _weighted_std(values: list[float], weights: list[float], mean: float) -> float:
    weight_total = sum(weights)
    if not values or weight_total <= 0:
        return 0.0
    variance = sum(
        weight * ((value - mean) ** 2) for value, weight in zip(values, weights, strict=True)
    ) / weight_total
    return math.sqrt(max(variance, 0.0))


def _circular_minute_distance(a: float, b: float) -> float:
    raw = abs(a - b)
    return min(raw, 1440.0 - raw)


def _recency_weight(anchor_time: dt.datetime, now: dt.datetime, half_life_days: int) -> float:
    age_days = max((now - anchor_time).total_seconds() / 86400.0, 0.0)
    return math.exp(-age_days / float(half_life_days))


def _round_score(value: float) -> float:
    return round(_clamp(value, 0.0, 1.0), 4)


def _build_reason_codes(
    interval_fit: float,
    time_fit: float,
    day_of_week_fit: float,
    recency_activity: float,
    timezone_name: str,
) -> list[str]:
    reason_codes: list[str] = []
    if interval_fit >= 0.7:
        reason_codes.append("consistent_interval")
    if time_fit >= 0.7:
        reason_codes.append("stable_time_of_day")
    if day_of_week_fit >= 0.5:
        reason_codes.append("stable_day_of_week")
    if recency_activity >= 0.7:
        reason_codes.append("recent_pattern_active")
    if timezone_name == "UTC":
        reason_codes.append("timezone_fallback_utc")
    return reason_codes


def _build_prediction_for_category(
    user: User,
    category: str,
    transactions: list[Transaction],
    now: dt.datetime,
) -> Prediction | None:
    settings = get_settings()
    min_transactions = settings.prediction.min_transactions_per_category
    if len(transactions) < min_transactions:
        return None

    ordered_transactions = sorted(transactions, key=lambda txn: _ensure_utc(txn.occurred_at))
    if len(ordered_transactions) < 3:
        return None

    timezone, timezone_name = _resolve_timezone(user)
    utc_times = [_ensure_utc(txn.occurred_at) for txn in ordered_transactions]
    local_times = [timestamp.astimezone(timezone) for timestamp in utc_times]

    intervals_seconds: list[float] = []
    interval_weights: list[float] = []
    for earlier, later in zip(utc_times, utc_times[1:]):
        interval_seconds = (later - earlier).total_seconds()
        if interval_seconds <= 0:
            continue
        intervals_seconds.append(interval_seconds)
        interval_weights.append(
            _recency_weight(later, now, settings.prediction.recency_half_life_days)
        )

    if len(intervals_seconds) < 2:
        return None

    average_interval_seconds = _weighted_mean(intervals_seconds, interval_weights)
    if average_interval_seconds <= 0:
        return None

    interval_std_seconds = _weighted_std(
        intervals_seconds,
        interval_weights,
        average_interval_seconds,
    )
    predicted_at = utc_times[-1] + dt.timedelta(seconds=average_interval_seconds)
    predicted_local = predicted_at.astimezone(timezone)

    historical_minutes = [
        local_time.hour * 60 + local_time.minute + (local_time.second / 60.0)
        for local_time in local_times
    ]
    predicted_minutes = (
        predicted_local.hour * 60
        + predicted_local.minute
        + (predicted_local.second / 60.0)
    )
    time_alignment_distance = _weighted_mean(
        [
            _circular_minute_distance(minute, predicted_minutes)
            for minute in historical_minutes
        ],
        [
            _recency_weight(local_time, now.astimezone(timezone), settings.prediction.recency_half_life_days)
            for local_time in local_times
        ],
    )

    day_of_week_weights = [
        _recency_weight(local_time, now.astimezone(timezone), settings.prediction.recency_half_life_days)
        for local_time in local_times
    ]
    same_day_weight = sum(
        weight
        for local_time, weight in zip(local_times, day_of_week_weights, strict=True)
        if local_time.weekday() == predicted_local.weekday()
    )
    total_day_weight = sum(day_of_week_weights) or 1.0

    interval_fit = 1.0 - _clamp(interval_std_seconds / average_interval_seconds, 0.0, 1.0)
    time_fit = math.exp(-(time_alignment_distance / 90.0))
    day_of_week_fit = same_day_weight / total_day_weight

    current_gap_seconds = max((now - utc_times[-1]).total_seconds(), 0.0)
    gap_ratio = current_gap_seconds / average_interval_seconds
    recency_activity = math.exp(-max(gap_ratio - 1.0, 0.0))

    probability = _round_score(
        (0.35 * interval_fit)
        + (0.25 * time_fit)
        + (0.15 * day_of_week_fit)
        + (0.25 * recency_activity)
    )
    sample_size_score = _clamp((len(ordered_transactions) - 2) / 4.0, 0.0, 1.0)
    confidence = _round_score(
        (0.45 * sample_size_score)
        + (0.35 * interval_fit)
        + (0.20 * time_fit)
    )

    window_std_minutes = interval_std_seconds / 60.0
    window_radius_minutes = int(
        round(
            _clamp(
                window_std_minutes,
                float(settings.prediction.window_floor_minutes),
                float(settings.prediction.window_cap_minutes),
            )
        )
    )
    window_delta = dt.timedelta(minutes=window_radius_minutes)
    reason_codes = _build_reason_codes(
        interval_fit=interval_fit,
        time_fit=time_fit,
        day_of_week_fit=day_of_week_fit,
        recency_activity=recency_activity,
        timezone_name=timezone_name,
    )

    return Prediction(
        category=category,
        predicted_at=predicted_at,
        window_start=predicted_at - window_delta,
        window_end=predicted_at + window_delta,
        probability=probability,
        confidence=confidence,
        support_count=len(ordered_transactions),
        reason_codes=reason_codes,
    )


def predict_for_user(
    db: Session,
    user_id: int,
    now: dt.datetime | None = None,
) -> list[Prediction]:
    settings = get_settings()
    current_time = _ensure_utc(now or dt.datetime.utcnow())
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        return []

    transactions = db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.occurred_at.asc())
    ).scalars().all()
    cutoff = current_time - dt.timedelta(days=settings.prediction.lookback_days)
    transactions = [
        transaction
        for transaction in transactions
        if _ensure_utc(transaction.occurred_at) >= cutoff
    ]

    grouped_transactions: dict[str, list[Transaction]] = defaultdict(list)
    for transaction in transactions:
        grouped_transactions[transaction.category].append(transaction)

    predictions: list[Prediction] = []
    for category, category_transactions in grouped_transactions.items():
        prediction = _build_prediction_for_category(
            user=user,
            category=category,
            transactions=category_transactions,
            now=current_time,
        )
        if prediction is not None:
            predictions.append(prediction)

    return sorted(
        predictions,
        key=lambda prediction: (
            prediction.probability,
            prediction.confidence,
            prediction.predicted_at,
        ),
        reverse=True,
    )
