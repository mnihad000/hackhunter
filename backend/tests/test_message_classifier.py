from __future__ import annotations

from backend.services.message_classifier import classify_message


def test_classify_transaction_message():
    assert classify_message("coffee 6.50") == "transaction"


def test_classify_command_message():
    assert classify_message("help") == "command"
    assert classify_message("/start") == "command"


def test_classify_feedback_message():
    assert classify_message("yes") == "feedback"
    assert classify_message("maybe") == "feedback"


def test_classify_unknown_message():
    assert classify_message("random words with no amount") == "unknown"
    assert classify_message("") == "unknown"

