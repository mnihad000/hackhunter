from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import create_app


def test_plaid_link_token_returns_token(monkeypatch):
    def fake_create_link_token(user):
        assert user.phone_number == "+15555559999"
        return "link-sandbox-test"

    monkeypatch.setattr("backend.routes.plaid.create_link_token", fake_create_link_token)

    app = create_app()
    with TestClient(app) as client:
        response = client.post("/plaid/link-token", json={"phone_number": "+15555559999"})

    assert response.status_code == 200
    assert response.json() == {"link_token": "link-sandbox-test"}


def test_plaid_exchange_stores_item_and_syncs(monkeypatch):
    monkeypatch.setattr(
        "backend.routes.plaid.exchange_public_token",
        lambda public_token: {"access_token": "access-sandbox-test", "item_id": "item-test"},
    )
    monkeypatch.setattr(
        "backend.routes.plaid.sync_plaid_item_transactions",
        lambda db, plaid_item: {"added": 2, "modified": 0, "removed": 0},
    )

    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/plaid/exchange-public-token",
            json={
                "phone_number": "+15555558888",
                "public_token": "public-sandbox-test",
                "institution_id": "ins_109508",
                "institution_name": "First Platypus Bank",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["plaid_item_id"] == "item-test"
    assert payload["institution_name"] == "First Platypus Bank"
    assert payload["sync"]["added"] == 2
