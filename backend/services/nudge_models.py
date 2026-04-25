from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field


class Prediction(BaseModel):
    category: str
    predicted_at: dt.datetime
    window_start: dt.datetime
    window_end: dt.datetime
    probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    support_count: int = Field(ge=0)
    reason_codes: list[str] = Field(default_factory=list)


class GoalContext(BaseModel):
    name: str
    target_amount: float
    current_amount: float
    remaining_amount: float


class RecentBehavior(BaseModel):
    category_last_7d_count: int = 0
    category_last_30d_count: int = 0
    total_last_7d_count: int = 0
    total_last_30d_count: int = 0
    average_category_amount_30d: float | None = None
    last_transaction_at: dt.datetime | None = None
    days_since_last_category_purchase: float | None = None


class ResponsePattern(BaseModel):
    feedback_count_30d: int = 0
    positive_feedback_count_30d: int = 0
    negative_feedback_count_30d: int = 0
    ignored_recent_nudges: int = 0
    last_feedback_at: dt.datetime | None = None


class RecentSpending(BaseModel):
    total_today: float = 0.0
    category_today: float = 0.0
    total_last_7d: float = 0.0
    category_last_7d: float = 0.0


class LastNudge(BaseModel):
    category: str | None = None
    sent_at: dt.datetime
    status: str
    urgency: str | None = None
    decision_source: str | None = None


class UserContext(BaseModel):
    goal: GoalContext | None = None
    goal_remaining: float | None = None
    recent_behavior: RecentBehavior
    response_pattern: ResponsePattern
    recent_spending: RecentSpending
    last_nudges: list[LastNudge] = Field(default_factory=list)
    timezone: str = "UTC"


class PolicyDecision(BaseModel):
    eligible: bool
    reason_codes: list[str] = Field(default_factory=list)
    blocked_by: str | None = None
    effective_cooldown_minutes: int = Field(ge=0)


class NudgeDecision(BaseModel):
    send: bool
    message: str = ""
    urgency: Literal["low", "medium", "high"]
    reasoning: str
    decision_source: Literal["gemini", "fallback_rule"]


class ProviderResult(BaseModel):
    success: bool
    status: str
    provider_message_sid: str | None = None
    error_message: str | None = None
