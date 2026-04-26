from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from backend.core.config import clear_settings_cache
from backend.db.session import clear_db_cache
from backend.main import create_app


def test_healthz_returns_200():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "piggybank-backend"


def test_readyz_fails_when_required_env_missing(monkeypatch):
    monkeypatch.setenv("DATABASE__URL", "")
    clear_settings_cache()

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert "DATABASE__URL is required." in payload["errors"]


def test_readyz_fails_when_schema_missing(monkeypatch, tmp_path: Path):
    sqlite_db_url = f"sqlite+pysqlite:///{tmp_path / 'readiness.db'}"
    monkeypatch.setenv("DATABASE__URL", sqlite_db_url)
    clear_settings_cache()
    clear_db_cache()

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    payload = response.json()
    assert payload["checks"]["database"] == "ok"
    assert payload["checks"]["schema"] == "error"
    assert any("database schema missing required tables" in err for err in payload["errors"])


def test_readyz_fails_when_plaid_columns_are_missing(monkeypatch, tmp_path: Path):
    sqlite_db_url = f"sqlite+pysqlite:///{tmp_path / 'readiness_partial.db'}"
    monkeypatch.setenv("DATABASE__URL", sqlite_db_url)
    clear_settings_cache()
    clear_db_cache()

    engine = create_engine(sqlite_db_url, future=True)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, phone_number VARCHAR(20) NOT NULL)"))
        connection.execute(
            text(
                "CREATE TABLE transactions ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "category VARCHAR(64) NOT NULL, "
                "amount NUMERIC(12, 2) NOT NULL, "
                "occurred_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE goals ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "name VARCHAR(120) NOT NULL, "
                "target_amount NUMERIC(12, 2) NOT NULL, "
                "current_amount NUMERIC(12, 2) NOT NULL, "
                "is_active BOOLEAN NOT NULL)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE feedback ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "message TEXT NOT NULL, "
                "received_at DATETIME NOT NULL)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE nudge_events ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "sent_at DATETIME NOT NULL, "
                "status VARCHAR(32) NOT NULL)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE plaid_items ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL, "
                "plaid_item_id VARCHAR(128) NOT NULL, "
                "access_token VARCHAR(255) NOT NULL, "
                "institution_name VARCHAR(120), "
                "sync_cursor TEXT)"
            )
        )

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/readyz")

    assert response.status_code == 503
    payload = response.json()
    assert payload["checks"]["database"] == "ok"
    assert payload["checks"]["schema"] == "error"
    assert any("database schema missing required columns" in err for err in payload["errors"])
