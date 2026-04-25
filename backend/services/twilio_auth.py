from __future__ import annotations

from typing import Mapping

from twilio.request_validator import RequestValidator

from backend.core.config import Environment, get_settings


def validate_twilio_request(
    url: str,
    form_data: Mapping[str, str],
    signature: str | None,
) -> bool:
    settings = get_settings()

    if settings.app.env == Environment.test:
        return True
    if not settings.twilio.validate_signature:
        return True
    if not signature:
        return False
    if not settings.twilio.auth_token:
        return False

    validator = RequestValidator(settings.twilio.auth_token)
    return validator.validate(url, dict(form_data), signature)

