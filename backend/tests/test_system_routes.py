from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

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
