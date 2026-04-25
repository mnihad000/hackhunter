from __future__ import annotations

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from backend.core.config import Environment, get_settings
from backend.services.nudge_models import ProviderResult


def send_sms(to: str, body: str) -> ProviderResult:
    settings = get_settings()
    if settings.app.env == Environment.test:
        return ProviderResult(
            success=True,
            status="sent",
            provider_message_sid="test-message-sid",
            error_message=None,
        )

    if not settings.twilio.account_sid or not settings.twilio.auth_token or not settings.twilio.phone_number:
        return ProviderResult(
            success=False,
            status="failed",
            provider_message_sid=None,
            error_message="Twilio configuration is incomplete.",
        )

    client = Client(settings.twilio.account_sid, settings.twilio.auth_token)
    try:
        response = client.messages.create(
            body=body,
            from_=settings.twilio.phone_number,
            to=to,
        )
        return ProviderResult(
            success=True,
            status=str(response.status or "sent"),
            provider_message_sid=response.sid,
            error_message=None,
        )
    except TwilioException as exc:
        return ProviderResult(
            success=False,
            status="failed",
            provider_message_sid=None,
            error_message=str(exc),
        )
