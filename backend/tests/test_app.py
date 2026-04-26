from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import create_app


def test_create_app_registers_expected_routes():
    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/healthz" in paths
    assert "/readyz" in paths
    assert "/sms" in paths
    assert "/plaid/link-token" in paths
    assert "/plaid/exchange-public-token" in paths
    assert "/plaid/sync" in paths
    assert "/plaid/webhook" in paths
    assert "/predict" in paths
    assert "/transactions" in paths
    assert "/goals" in paths


def test_cors_preflight_allows_configured_origin(monkeypatch):
    monkeypatch.setenv("APP__CORS_ORIGINS", "https://piggybank.vercel.app")

    app = create_app()
    with TestClient(app) as client:
        response = client.options(
            "/predict",
            headers={
                "Origin": "https://piggybank.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://piggybank.vercel.app"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "Content-Type" in response.headers["access-control-allow-headers"]


def test_cors_does_not_allow_unknown_origin(monkeypatch):
    monkeypatch.setenv("APP__CORS_ORIGINS", "https://piggybank.vercel.app")

    app = create_app()
    with TestClient(app) as client:
        response = client.options(
            "/predict",
            headers={
                "Origin": "https://unknown.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

    assert "access-control-allow-origin" not in response.headers
