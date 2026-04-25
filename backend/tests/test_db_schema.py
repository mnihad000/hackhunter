from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.core.config import clear_settings_cache
from backend.db.base import Base
from backend.db.session import check_required_tables, clear_db_cache
from backend.models import Transaction, User


@pytest.fixture
def sqlite_db_url(tmp_path: Path) -> str:
    return f"sqlite+pysqlite:///{tmp_path / 'schema_test.db'}"


def test_required_tables_exist_after_create_all(monkeypatch, sqlite_db_url: str):
    monkeypatch.setenv("DATABASE__URL", sqlite_db_url)
    clear_settings_cache()
    clear_db_cache()

    engine = create_engine(sqlite_db_url, future=True)
    Base.metadata.create_all(bind=engine)

    ok, missing = check_required_tables(
        {"users", "transactions", "goals", "feedback", "nudge_events", "plaid_items"},
        sqlite_db_url,
    )
    assert ok is True
    assert missing == []


def test_user_phone_number_is_unique(monkeypatch, sqlite_db_url: str):
    monkeypatch.setenv("DATABASE__URL", sqlite_db_url)
    clear_settings_cache()
    clear_db_cache()

    engine = create_engine(sqlite_db_url, future=True)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_local() as session:
        session.add(User(phone_number="+15555551212"))
        session.commit()

    with session_local() as session:
        session.add(User(phone_number="+15555551212"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_transaction_declares_fk_to_users():
    fk_targets = {fk.target_fullname for fk in Transaction.__table__.foreign_keys}
    assert "users.id" in fk_targets

