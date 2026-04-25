from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.db.session import get_engine
from backend.models import Transaction, User
from backend.services.prediction import predict_for_user


def _db_session() -> Session:
    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    return Session(engine)


def test_predict_for_user_returns_regular_after_work_pattern():
    now = dt.datetime(2026, 4, 24, 21, 25, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15550000001", timezone="America/New_York")
        db.add(user)
        db.commit()
        db.refresh(user)

        transaction_times = [
            dt.datetime(2026, 4, 20, 21, 30),
            dt.datetime(2026, 4, 21, 21, 30),
            dt.datetime(2026, 4, 22, 21, 30),
            dt.datetime(2026, 4, 23, 21, 30),
        ]
        for occurred_at in transaction_times:
            db.add(
                Transaction(
                    user_id=user.id,
                    category="food",
                    amount=Decimal("14.00"),
                    occurred_at=occurred_at,
                )
            )
        db.commit()

        predictions = predict_for_user(db, user.id, now=now)

    assert len(predictions) == 1
    prediction = predictions[0]
    assert prediction.category == "food"
    assert prediction.probability >= 0.75
    assert prediction.confidence >= 0.6
    assert prediction.support_count == 4
    assert "consistent_interval" in prediction.reason_codes
    assert prediction.predicted_at.astimezone(dt.timezone.utc).hour == 21
    assert prediction.predicted_at.astimezone(dt.timezone.utc).minute == 30
    assert prediction.predicted_at.astimezone(dt.timezone(dt.timedelta(hours=-4))).hour == 17


def test_predict_for_user_returns_lower_quality_for_irregular_history():
    now = dt.datetime(2026, 4, 25, 18, 0, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15550000002", timezone="America/New_York")
        db.add(user)
        db.commit()
        db.refresh(user)

        transaction_times = [
            dt.datetime(2026, 4, 2, 12, 0),
            dt.datetime(2026, 4, 8, 21, 15),
            dt.datetime(2026, 4, 19, 9, 45),
            dt.datetime(2026, 4, 24, 23, 5),
        ]
        for occurred_at in transaction_times:
            db.add(
                Transaction(
                    user_id=user.id,
                    category="coffee",
                    amount=Decimal("6.50"),
                    occurred_at=occurred_at,
                )
            )
        db.commit()

        predictions = predict_for_user(db, user.id, now=now)

    assert len(predictions) == 1
    prediction = predictions[0]
    assert prediction.probability < 0.75
    assert prediction.confidence < 0.65


def test_predict_for_user_skips_sparse_histories():
    now = dt.datetime(2026, 4, 24, 21, 25, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15550000003")
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add_all(
            [
                Transaction(
                    user_id=user.id,
                    category="snacks",
                    amount=Decimal("3.00"),
                    occurred_at=dt.datetime(2026, 4, 21, 18, 0),
                ),
                Transaction(
                    user_id=user.id,
                    category="snacks",
                    amount=Decimal("4.00"),
                    occurred_at=dt.datetime(2026, 4, 22, 18, 0),
                ),
            ]
        )
        db.commit()

        predictions = predict_for_user(db, user.id, now=now)

    assert predictions == []


def test_predict_for_user_uses_timezone_fallback_when_missing_timezone():
    now = dt.datetime(2026, 4, 24, 21, 25, tzinfo=dt.timezone.utc)
    with _db_session() as db:
        user = User(phone_number="+15550000004")
        db.add(user)
        db.commit()
        db.refresh(user)
        for day in range(20, 24):
            db.add(
                Transaction(
                    user_id=user.id,
                    category="food",
                    amount=Decimal("10.00"),
                    occurred_at=dt.datetime(2026, 4, day, 21, 30),
                )
            )
        db.commit()

        predictions = predict_for_user(db, user.id, now=now)

    assert len(predictions) == 1
    assert "timezone_fallback_utc" in predictions[0].reason_codes
