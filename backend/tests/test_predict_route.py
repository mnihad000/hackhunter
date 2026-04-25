from __future__ import annotations

import datetime as dt
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.session import get_engine
from backend.main import create_app
from backend.models import Transaction, User


def _db_session() -> Session:
    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    return Session(engine)


def test_predict_route_returns_prediction_payload():
    current_now = dt.datetime.utcnow().replace(minute=30, second=0, microsecond=0)
    with _db_session() as db:
        user = User(phone_number="+15554440001", timezone="America/New_York")
        db.add(user)
        db.commit()
        db.refresh(user)
        for day_offset in [4, 3, 2, 1]:
            db.add(
                Transaction(
                    user_id=user.id,
                    category="food",
                    amount=Decimal("12.00"),
                    occurred_at=current_now - dt.timedelta(days=day_offset),
                )
            )
        db.commit()
        user_id = user.id

    app = create_app()
    with TestClient(app) as client:
        response = client.get(f"/predict?user_id={user_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user_id
    assert len(payload["predictions"]) == 1
    prediction = payload["predictions"][0]
    assert prediction["category"] == "food"
    assert "predicted_at" in prediction
    assert "window_start" in prediction
    assert "window_end" in prediction
    assert "probability" in prediction
    assert "confidence" in prediction


def test_predict_route_requires_identifier():
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/predict")

    assert response.status_code == 400
    assert response.json()["detail"] == "Provide user_id or phone_number."
