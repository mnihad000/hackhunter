from __future__ import annotations

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
