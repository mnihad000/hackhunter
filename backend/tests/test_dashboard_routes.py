from __future__ import annotations

import datetime as dt
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.session import get_engine
from backend.main import create_app
from backend.models import Goal, Transaction, User


def _db_session() -> Session:
    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    return Session(engine)


def test_get_transactions_returns_recent_transactions_descending():
    with _db_session() as db:
        user = User(phone_number="+15557770001")
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add_all(
            [
                Transaction(
                    user_id=user.id,
                    category="coffee",
                    amount=Decimal("6.50"),
                    occurred_at=dt.datetime(2026, 4, 24, 8, 30),
                ),
                Transaction(
                    user_id=user.id,
                    category="food",
                    amount=Decimal("12.00"),
                    occurred_at=dt.datetime(2026, 4, 24, 18, 15),
                ),
            ]
        )
        db.commit()
        user_id = user.id

    app = create_app()
    with TestClient(app) as client:
        response = client.get(f"/transactions?user_id={user_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user_id
    assert [item["category"] for item in payload["transactions"]] == ["food", "coffee"]
    assert payload["transactions"][0]["amount"] == 12.0
    assert "occurred_at" in payload["transactions"][0]


def test_get_goals_returns_active_goal_with_remaining_amount():
    with _db_session() as db:
        user = User(phone_number="+15557770002")
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add(
            Goal(
                user_id=user.id,
                name="Bike",
                target_amount=Decimal("250.00"),
                current_amount=Decimal("75.00"),
                is_active=True,
            )
        )
        db.commit()
        user_id = user.id

    app = create_app()
    with TestClient(app) as client:
        response = client.get(f"/goals?user_id={user_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user_id
    assert payload["goal"]["name"] == "Bike"
    assert payload["goal"]["remaining_amount"] == 175.0
    assert payload["goal"]["is_active"] is True


def test_patch_goals_updates_existing_active_goal():
    with _db_session() as db:
        user = User(phone_number="+15557770003")
        db.add(user)
        db.commit()
        db.refresh(user)
        goal = Goal(
            user_id=user.id,
            name="Bike",
            target_amount=Decimal("250.00"),
            current_amount=Decimal("100.00"),
            is_active=True,
        )
        db.add(goal)
        db.commit()
        user_id = user.id

    app = create_app()
    with TestClient(app) as client:
        response = client.patch(
            f"/goals?user_id={user_id}",
            json={
                "name": "Laptop",
                "target_amount": "1200.00",
                "current_amount": "300.00",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["goal"]["name"] == "Laptop"
    assert payload["goal"]["target_amount"] == 1200.0
    assert payload["goal"]["current_amount"] == 300.0
    assert payload["goal"]["remaining_amount"] == 900.0


def test_patch_goals_creates_goal_when_missing():
    with _db_session() as db:
        user = User(phone_number="+15557770004")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    app = create_app()
    with TestClient(app) as client:
        response = client.patch(
            f"/goals?user_id={user_id}",
            json={
                "name": "Emergency Fund",
                "target_amount": "500.00",
                "current_amount": "25.00",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["goal"]["name"] == "Emergency Fund"
    assert payload["goal"]["target_amount"] == 500.0
    assert payload["goal"]["current_amount"] == 25.0
    assert payload["goal"]["remaining_amount"] == 475.0
    assert payload["goal"]["is_active"] is True


def test_patch_goals_requires_creation_fields_when_missing_goal():
    with _db_session() as db:
        user = User(phone_number="+15557770005")
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    app = create_app()
    with TestClient(app) as client:
        response = client.patch(f"/goals?user_id={user_id}", json={"current_amount": "10.00"})

    assert response.status_code == 400
    assert response.json()["detail"] == "name and target_amount are required when creating a goal."
