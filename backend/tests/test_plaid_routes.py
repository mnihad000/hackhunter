from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.session import get_engine
from backend.main import create_app
from backend.models import PlaidItem, Transaction, User


def _db_session() -> Session:
    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    return Session(engine)


def test_plaid_link_token_route_returns_token_and_creates_user(monkeypatch):
    def fake_request(path: str, payload: dict[str, object]) -> dict[str, object]:
        assert path == "/link/token/create"
        return {"link_token": "link-sandbox-token", "expiration": "2026-04-26T00:00:00Z"}

    monkeypatch.setattr("backend.services.plaid._request_plaid", fake_request)

    app = create_app()
    with TestClient(app) as client:
        response = client.post("/plaid/link-token?phone_number=+15558880000")

    assert response.status_code == 200
    payload = response.json()
    assert payload["link_token"] == "link-sandbox-token"

    with _db_session() as db:
        user = db.execute(select(User).where(User.phone_number == "+15558880000")).scalar_one()

    assert user.phone_number == "+15558880000"


def test_plaid_exchange_imports_transactions_and_persists_item(monkeypatch):
    def fake_request(path: str, payload: dict[str, object]) -> dict[str, object]:
        if path == "/item/public_token/exchange":
            return {"access_token": "access-sandbox-123", "item_id": "item-sandbox-123"}
        if path == "/transactions/get":
            return {
                "transactions": [
                    {
                        "transaction_id": "plaid-txn-1",
                        "amount": 12.5,
                        "date": "2026-04-24",
                        "merchant_name": "Coffee Shop",
                        "personal_finance_category": {"primary": "FOOD_AND_DRINK"},
                    }
                ],
                "total_transactions": 1,
            }
        raise AssertionError(f"Unexpected Plaid path: {path}")

    monkeypatch.setattr("backend.services.plaid._request_plaid", fake_request)

    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/plaid/exchange-public-token?phone_number=+15558880001",
            json={"public_token": "public-sandbox-token", "institution_name": "Plaid Bank"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["plaid_item_id"] == "item-sandbox-123"
    assert payload["imported_count"] == 1

    with _db_session() as db:
        user = db.execute(select(User).where(User.phone_number == "+15558880001")).scalar_one()
        plaid_item = db.execute(select(PlaidItem).where(PlaidItem.user_id == user.id)).scalar_one()
        transaction = db.execute(select(Transaction).where(Transaction.user_id == user.id)).scalar_one()

    assert plaid_item.institution_name == "Plaid Bank"
    assert transaction.source == "plaid"
    assert transaction.plaid_transaction_id == "plaid-txn-1"
    assert transaction.merchant_name == "Coffee Shop"
    assert transaction.category == "food_and_drink"


def test_plaid_sync_is_idempotent_and_tracks_cursor(monkeypatch):
    responses = [
        {
            "added": [
                {
                    "transaction_id": "plaid-sync-1",
                    "amount": 18.25,
                    "date": "2026-04-23",
                    "name": "Groceries",
                    "personal_finance_category": {"primary": "GROCERIES"},
                }
            ],
            "modified": [],
            "removed": [],
            "next_cursor": "cursor-1",
            "has_more": False,
        },
        {
            "added": [
                {
                    "transaction_id": "plaid-sync-1",
                    "amount": 18.25,
                    "date": "2026-04-23",
                    "name": "Groceries",
                    "personal_finance_category": {"primary": "GROCERIES"},
                }
            ],
            "modified": [],
            "removed": [],
            "next_cursor": "cursor-2",
            "has_more": False,
        },
    ]

    def fake_request(path: str, payload: dict[str, object]) -> dict[str, object]:
        if path == "/item/public_token/exchange":
            return {"access_token": "access-sandbox-456", "item_id": "item-sandbox-456"}
        if path == "/transactions/get":
            return {"transactions": [], "total_transactions": 0}
        if path == "/transactions/sync":
            return responses.pop(0)
        raise AssertionError(f"Unexpected Plaid path: {path}")

    monkeypatch.setattr("backend.services.plaid._request_plaid", fake_request)

    app = create_app()
    with TestClient(app) as client:
        exchange_response = client.post(
            "/plaid/exchange-public-token?phone_number=+15558880002",
            json={"public_token": "public-sandbox-token"},
        )
        assert exchange_response.status_code == 200

        first_sync = client.post("/plaid/sync?phone_number=+15558880002")
        second_sync = client.post("/plaid/sync?phone_number=+15558880002")

    assert first_sync.status_code == 200
    assert first_sync.json()["imported_count"] == 1
    assert second_sync.status_code == 200
    assert second_sync.json()["imported_count"] == 0

    with _db_session() as db:
        user = db.execute(select(User).where(User.phone_number == "+15558880002")).scalar_one()
        plaid_item = db.execute(select(PlaidItem).where(PlaidItem.user_id == user.id)).scalar_one()
        transactions = db.execute(select(Transaction).where(Transaction.user_id == user.id)).scalars().all()

    assert plaid_item.sync_cursor == "cursor-2"
    assert len(transactions) == 1


def test_plaid_webhook_syncs_known_item(monkeypatch):
    def fake_request(path: str, payload: dict[str, object]) -> dict[str, object]:
        if path == "/item/public_token/exchange":
            return {"access_token": "access-sandbox-789", "item_id": "item-sandbox-789"}
        if path == "/transactions/get":
            return {"transactions": [], "total_transactions": 0}
        if path == "/transactions/sync":
            return {
                "added": [
                    {
                        "transaction_id": "plaid-webhook-1",
                        "amount": 41.0,
                        "date": "2026-04-25",
                        "merchant_name": "Ride Share",
                        "personal_finance_category": {"primary": "TRANSPORTATION"},
                    }
                ],
                "modified": [],
                "removed": [],
                "next_cursor": "cursor-webhook-1",
                "has_more": False,
            }
        raise AssertionError(f"Unexpected Plaid path: {path}")

    monkeypatch.setattr("backend.services.plaid._request_plaid", fake_request)

    app = create_app()
    with TestClient(app) as client:
        exchange_response = client.post(
            "/plaid/exchange-public-token?phone_number=+15558880003",
            json={"public_token": "public-sandbox-token"},
        )
        assert exchange_response.status_code == 200

        webhook_response = client.post(
            "/plaid/webhook",
            json={
                "webhook_type": "TRANSACTIONS",
                "webhook_code": "SYNC_UPDATES_AVAILABLE",
                "item_id": "item-sandbox-789",
            },
        )

    assert webhook_response.status_code == 200
    payload = webhook_response.json()
    assert payload["status"] == "synced"
    assert payload["imported_count"] == 1
