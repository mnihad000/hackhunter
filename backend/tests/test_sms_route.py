from __future__ import annotations

import datetime as dt
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import clear_settings_cache, get_settings
from backend.db.session import get_engine
from backend.main import create_app
from backend.models import Feedback, NudgeEvent, Transaction, User


def _db_session() -> Session:
    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    return Session(engine)


def test_sms_returns_twiml_200_for_valid_payload():
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/sms", data={"From": "+15555550000", "Body": "coffee 6.50"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Response>" in response.text
    assert "Oink. Logged coffee $6.50." in response.text

    settings = get_settings()
    engine = get_engine(settings.database.url, settings.database.echo)  # type: ignore[arg-type]
    with Session(engine) as db:
        users = db.execute(select(User)).scalars().all()
        transactions = db.execute(select(Transaction)).scalars().all()
        assert len(users) == 1
        assert users[0].phone_number == "+15555550000"
        assert len(transactions) == 1
        assert transactions[0].user_id == users[0].id
        assert transactions[0].amount == Decimal("6.50")
        assert transactions[0].source == "sms"


def test_sms_empty_body_classifies_unknown():
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/sms", data={"From": "+15555550000", "Body": ""})

    assert response.status_code == 200
    assert "I did not understand that. Try: coffee 6.50" in response.text


def test_sms_invalid_transaction_returns_format_guidance():
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/sms", data={"From": "+15555550000", "Body": "coffee -1"})

    assert response.status_code == 200
    assert "Could not log that. Use format: coffee 6.50" in response.text


def test_sms_invalid_signature_rejected_outside_test_mode(monkeypatch):
    monkeypatch.setenv("APP__ENV", "local")
    monkeypatch.setenv("TWILIO__VALIDATE_SIGNATURE", "true")
    monkeypatch.setenv("TWILIO__AUTH_TOKEN", "test-token")
    monkeypatch.setenv("TWILIO__ACCOUNT_SID", "AC123")
    monkeypatch.setenv("TWILIO__PHONE_NUMBER", "+15555550000")
    monkeypatch.setenv("GEMINI__API_KEY", "gem-key")
    clear_settings_cache()

    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/sms",
            data={"From": "+15555550000", "Body": "coffee 6.50"},
            headers={"X-Twilio-Signature": "invalid"},
        )

    assert response.status_code == 403


def test_sms_signature_bypassed_in_test_mode():
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/sms",
            data={"From": "+15555550000", "Body": "help"},
            headers={"X-Twilio-Signature": "invalid"},
        )

    assert response.status_code == 200
    assert "Command received. More commands are coming soon." in response.text


def test_sms_feedback_returns_feedback_ack():
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/sms",
            data={"From": "+15555550000", "Body": "maybe"},
            headers={"X-Twilio-Signature": "invalid"},
        )

    assert response.status_code == 200
    assert "Got your reply. Thanks." in response.text

    with _db_session() as db:
        feedback_entries = db.execute(select(Feedback)).scalars().all()
        users = db.execute(select(User)).scalars().all()
        assert len(users) == 1
        assert len(feedback_entries) == 1
        assert feedback_entries[0].user_id == users[0].id
        assert feedback_entries[0].response_type == "neutral"


def test_sms_triggers_demo_nudge_after_three_same_category_messages():
    app = create_app()
    with TestClient(app) as client:
        client.post("/sms", data={"From": "+15555550001", "Body": "coffee 6.50"})
        client.post("/sms", data={"From": "+15555550001", "Body": "coffee 6.75"})
        response = client.post("/sms", data={"From": "+15555550001", "Body": "coffee 9"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "Oink. Logged coffee $9.00." in response.text

    with _db_session() as db:
        events = db.execute(select(NudgeEvent).order_by(NudgeEvent.id.asc())).scalars().all()
        assert len(events) == 1
        event = events[0]
        assert event.category == "coffee"
        assert event.status == "sent"
        assert event.decision_source == "rapid_repeat_demo"
        assert event.provider_message_sid == "test-message-sid"
        assert event.message_body is not None
        assert "$22.25" in event.message_body
        assert "not spending on coffee today" in event.message_body


def test_sms_two_same_category_messages_do_not_trigger_demo_nudge():
    app = create_app()
    with TestClient(app) as client:
        client.post("/sms", data={"From": "+15555550002", "Body": "coffee 6.50"})
        response = client.post("/sms", data={"From": "+15555550002", "Body": "coffee 6.75"})

    assert response.status_code == 200

    with _db_session() as db:
        events = db.execute(select(NudgeEvent)).scalars().all()
        assert len(events) == 0


def test_sms_three_messages_outside_five_minute_window_do_not_trigger_demo_nudge():
    baseline_time = dt.datetime.utcnow().replace(second=0, microsecond=0)
    with _db_session() as db:
        user = User(phone_number="+15555550003")
        db.add(user)
        db.commit()
        db.refresh(user)
        db.add_all(
            [
                Transaction(
                    user_id=user.id,
                    category="coffee",
                    amount=Decimal("4.00"),
                    source="sms",
                    occurred_at=baseline_time - dt.timedelta(minutes=12),
                ),
                Transaction(
                    user_id=user.id,
                    category="coffee",
                    amount=Decimal("5.00"),
                    source="sms",
                    occurred_at=baseline_time - dt.timedelta(minutes=7),
                ),
            ]
        )
        db.commit()

    app = create_app()
    with TestClient(app) as client:
        response = client.post("/sms", data={"From": "+15555550003", "Body": "coffee 6.50"})

    assert response.status_code == 200

    with _db_session() as db:
        events = db.execute(select(NudgeEvent)).scalars().all()
        assert len(events) == 0


def test_sms_mixed_categories_do_not_trigger_demo_nudge():
    app = create_app()
    with TestClient(app) as client:
        client.post("/sms", data={"From": "+15555550004", "Body": "coffee 6.50"})
        client.post("/sms", data={"From": "+15555550004", "Body": "tea 3.25"})
        response = client.post("/sms", data={"From": "+15555550004", "Body": "coffee 7"})

    assert response.status_code == 200

    with _db_session() as db:
        events = db.execute(select(NudgeEvent)).scalars().all()
        assert len(events) == 0


def test_sms_reuses_existing_user_for_same_phone():
    app = create_app()
    with TestClient(app) as client:
        client.post("/sms", data={"From": "+15555550000", "Body": "coffee 6.50"})
        response = client.post("/sms", data={"From": "+15555550000", "Body": "tea 3.25"})

    assert response.status_code == 200

    with _db_session() as db:
        user_count = db.execute(select(User)).scalars().all()
        txns = db.execute(select(Transaction).order_by(Transaction.id)).scalars().all()
        assert len(user_count) == 1
        assert len(txns) == 2
        assert txns[0].user_id == txns[1].user_id
