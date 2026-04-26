from __future__ import annotations

from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.demo_nudge import maybe_send_rapid_repeat_demo_nudge
from backend.services.feedback_service import save_feedback
from backend.services.message_classifier import classify_message
from backend.services.sms_replies import build_sms_reply
from backend.services.transaction_parser import TransactionParseError, parse_transaction
from backend.services.transaction_service import save_transaction
from backend.services.twilio_auth import validate_twilio_request
from backend.services.user_service import get_or_create_user_by_phone

router = APIRouter(tags=["sms"])


def _twiml_message(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(body)}</Message></Response>'


@router.post("/sms")
async def receive_sms(request: Request, db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    normalized_form = {str(key): str(value) for key, value in form.items()}

    signature = request.headers.get("X-Twilio-Signature")
    if not validate_twilio_request(str(request.url), normalized_form, signature):
        return Response(content="Forbidden", status_code=403, media_type="text/plain")

    sender = normalized_form.get("From", "").strip()
    message = normalized_form.get("Body")
    kind = classify_message(message)

    if kind == "transaction":
        try:
            parsed = parse_transaction(message or "")
        except TransactionParseError:
            reply = build_sms_reply("transaction", {"ok": False})
            return Response(content=_twiml_message(reply), status_code=200, media_type="application/xml")

        if not sender:
            reply = "Missing sender number."
            return Response(content=_twiml_message(reply), status_code=400, media_type="application/xml")

        user = get_or_create_user_by_phone(db, sender)
        transaction = save_transaction(
            db=db,
            user_id=user.id,
            category=parsed.category,
            amount=parsed.amount,
        )
        maybe_send_rapid_repeat_demo_nudge(
            db=db,
            user=user,
            category=parsed.category,
            latest_occurred_at=transaction.occurred_at,
        )
        reply = build_sms_reply(
            "transaction",
            {"ok": True, "category": parsed.category, "amount": f"{parsed.amount:.2f}"},
        )
        return Response(content=_twiml_message(reply), status_code=200, media_type="application/xml")

    if kind == "feedback" and sender:
        user = get_or_create_user_by_phone(db, sender)
        save_feedback(db=db, user_id=user.id, message=message or "")

    reply = build_sms_reply(kind)
    twiml = _twiml_message(reply)
    return Response(content=twiml, status_code=200, media_type="application/xml")
