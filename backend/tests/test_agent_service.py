from __future__ import annotations

import datetime as dt

from backend.services import agent
from backend.services.nudge_models import (
    GoalContext,
    Prediction,
    RecentBehavior,
    RecentSpending,
    ResponsePattern,
    UserContext,
)


def _prediction() -> Prediction:
    return Prediction(
        category="food",
        predicted_at=dt.datetime(2026, 4, 25, 21, 30, tzinfo=dt.timezone.utc),
        window_start=dt.datetime(2026, 4, 25, 21, 0, tzinfo=dt.timezone.utc),
        window_end=dt.datetime(2026, 4, 25, 22, 0, tzinfo=dt.timezone.utc),
        probability=0.84,
        confidence=0.77,
        support_count=5,
        reason_codes=["consistent_interval", "stable_time_of_day"],
    )


def _user_context() -> UserContext:
    return UserContext(
        goal=GoalContext(
            name="Bike",
            target_amount=250.0,
            current_amount=220.0,
            remaining_amount=30.0,
        ),
        goal_remaining=30.0,
        recent_behavior=RecentBehavior(
            category_last_7d_count=4,
            category_last_30d_count=12,
            total_last_7d_count=8,
            total_last_30d_count=20,
        ),
        response_pattern=ResponsePattern(
            feedback_count_30d=2,
            positive_feedback_count_30d=1,
            negative_feedback_count_30d=0,
            ignored_recent_nudges=1,
        ),
        recent_spending=RecentSpending(total_today=35.0, category_today=12.0, total_last_7d=90.0, category_last_7d=48.0),
        last_nudges=[],
        timezone="America/New_York",
    )


def test_decide_and_generate_nudge_parses_json_response(monkeypatch):
    monkeypatch.setattr(
        agent,
        "_call_gemini",
        lambda prompt: {
            "send": True,
            "message": "You usually grab food after work. Want the healthier option today?",
            "urgency": "medium",
            "reasoning": "Consistent evening spend with meaningful goal proximity.",
        },
    )

    decision = agent.decide_and_generate_nudge(_prediction(), _user_context())

    assert decision.send is True
    assert decision.decision_source == "gemini"
    assert decision.urgency == "medium"
    assert "healthier option" in decision.message


def test_decide_and_generate_nudge_falls_back_on_invalid_response(monkeypatch):
    monkeypatch.setattr(agent, "_call_gemini", lambda prompt: (_ for _ in ()).throw(ValueError("bad json")))

    decision = agent.decide_and_generate_nudge(_prediction(), _user_context())

    assert decision.decision_source == "fallback_rule"
    assert decision.send is True
    assert decision.message
    assert "Gemini failed" in decision.reasoning


def test_build_agent_prompt_keeps_prediction_and_context_separate():
    prompt = agent.build_agent_prompt(_prediction(), _user_context())

    assert "prediction_data" in prompt
    assert "user_context" in prompt
    assert "Do not alter, invent, or reinterpret numeric prediction fields." in prompt
