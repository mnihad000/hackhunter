from __future__ import annotations

import re
from typing import Literal

MessageKind = Literal["transaction", "feedback", "command", "unknown"]

_TRANSACTION_PATTERN = re.compile(
    r"^\s*[a-zA-Z][a-zA-Z0-9_\-\s]{0,40}\s+\$?\d+(?:\.\d{1,2})?\s*$"
)
_COMMANDS = {
    "help",
    "goals",
    "goal",
    "/start",
    "start",
    "stop",
    "pause",
    "resume",
    "settings",
}
_FEEDBACK_WORDS = {
    "yes",
    "y",
    "no",
    "n",
    "maybe",
    "ok",
    "okay",
    "nah",
    "skip",
}


def _looks_like_transaction_candidate(normalized: str) -> bool:
    parts = normalized.split()
    if len(parts) < 2:
        return False

    amount_candidate = parts[-1]
    return amount_candidate.startswith("$") or any(char.isdigit() for char in amount_candidate)


def classify_message(text: str | None) -> MessageKind:
    if text is None:
        return "unknown"

    normalized = text.strip()
    if not normalized:
        return "unknown"

    lowered = normalized.lower()
    if lowered in _COMMANDS:
        return "command"
    if lowered in _FEEDBACK_WORDS:
        return "feedback"
    if _TRANSACTION_PATTERN.match(normalized):
        return "transaction"
    if _looks_like_transaction_candidate(normalized):
        return "transaction"
    return "unknown"
