from __future__ import annotations

from typing import Any

from backend.services.message_classifier import MessageKind


def build_sms_reply(kind: MessageKind, context: dict[str, Any] | None = None) -> str:
    payload = context or {}

    if kind == "transaction":
        if payload.get("ok"):
            category = payload.get("category", "purchase")
            amount = payload.get("amount", "0.00")
            return f"Oink. Logged {category} ${amount}."
        return "Could not log that. Use format: coffee 6.50"

    if kind == "feedback":
        return "Got your reply. Thanks."

    if kind == "command":
        return "Command received. More commands are coming soon."

    return "I did not understand that. Try: coffee 6.50"

