from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.core.config import clear_settings_cache, get_settings
from backend.core.exceptions import ConfigValidationError
from backend.main import create_app


def test_settings_load_from_env_and_cast_types_correctly(monkeypatch):
    monkeypatch.setenv("APP__ENV", "local")
    monkeypatch.setenv("APP__DEBUG", "true")
    monkeypatch.setenv("APP__PORT", "9090")
    monkeypatch.setenv("DATABASE__URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("TWILIO__ACCOUNT_SID", "AC123")
    monkeypatch.setenv("TWILIO__AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO__PHONE_NUMBER", "+15555550000")
    monkeypatch.setenv("GEMINI__API_KEY", "gem-key")
    monkeypatch.setenv("GEMINI__TIMEOUT_SECONDS", "12")
    monkeypatch.setenv("SCHEDULER__INTERVAL_SECONDS", "45")
    monkeypatch.setenv("PREDICTION__NUDGE_PROBABILITY_THRESHOLD", "0.7")
    monkeypatch.setenv("PREDICTION__NUDGE_COOLDOWN_MINUTES", "30")
    monkeypatch.setenv("PREDICTION__LOOKBACK_DAYS", "120")
    monkeypatch.setenv("PREDICTION__MIN_TRANSACTIONS_PER_CATEGORY", "4")
    monkeypatch.setenv("PREDICTION__RECENCY_HALF_LIFE_DAYS", "10")
    monkeypatch.setenv("PREDICTION__WINDOW_FLOOR_MINUTES", "20")
    monkeypatch.setenv("PREDICTION__WINDOW_CAP_MINUTES", "90")
    monkeypatch.setenv("PREDICTION__MAX_CANDIDATES_PER_USER", "2")
    clear_settings_cache()

    settings = get_settings()

    assert settings.app.debug is True
    assert settings.app.port == 9090
    assert settings.gemini.timeout_seconds == 12
    assert settings.scheduler.interval_seconds == 45
    assert settings.prediction.nudge_probability_threshold == 0.7
    assert settings.prediction.nudge_cooldown_minutes == 30
    assert settings.prediction.lookback_days == 120
    assert settings.prediction.min_transactions_per_category == 4
    assert settings.prediction.recency_half_life_days == 10
    assert settings.prediction.window_floor_minutes == 20
    assert settings.prediction.window_cap_minutes == 90
    assert settings.prediction.max_candidates_per_user == 2


def test_prod_mode_rejects_insecure_or_missing_required_config(monkeypatch):
    monkeypatch.setenv("APP__ENV", "prod")
    monkeypatch.setenv("APP__DEBUG", "true")
    monkeypatch.setenv("DATABASE__URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.delenv("TWILIO__ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO__AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO__PHONE_NUMBER", raising=False)
    monkeypatch.delenv("GEMINI__API_KEY", raising=False)
    clear_settings_cache()

    app = create_app()
    with pytest.raises(ConfigValidationError):
        with TestClient(app):
            pass
