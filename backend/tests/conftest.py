from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from pathlib import Path

from backend.core.config import clear_settings_cache
from backend.db.base import Base
from backend.db.session import clear_db_cache
from backend.models import Feedback, Goal, NudgeEvent, Transaction, User

_ = (User, Transaction, Goal, Feedback, NudgeEvent)


@pytest.fixture(autouse=True)
def _default_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "test_backend.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    monkeypatch.setenv("APP__ENV", "test")
    monkeypatch.setenv("APP__DEBUG", "false")
    monkeypatch.setenv("DATABASE__URL", db_url)
    monkeypatch.setenv("SCHEDULER__INTERVAL_SECONDS", "60")
    monkeypatch.setenv("PREDICTION__NUDGE_PROBABILITY_THRESHOLD", "0.65")
    monkeypatch.setenv("PREDICTION__NUDGE_COOLDOWN_MINUTES", "120")

    clear_settings_cache()
    clear_db_cache()
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(bind=engine)
    engine.dispose()
    yield
    clear_settings_cache()
    clear_db_cache()
