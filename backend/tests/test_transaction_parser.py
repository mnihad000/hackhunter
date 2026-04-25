from __future__ import annotations

from decimal import Decimal

import pytest

from backend.services.transaction_parser import TransactionParseError, parse_transaction


def test_parse_transaction_valid():
    parsed = parse_transaction("coffee 6.50")
    assert parsed.category == "coffee"
    assert parsed.amount == Decimal("6.50")


def test_parse_transaction_valid_multi_word_category():
    parsed = parse_transaction("Late Night Snacks 12.00")
    assert parsed.category == "late night snacks"
    assert parsed.amount == Decimal("12.00")


def test_parse_transaction_invalid_amount_text():
    with pytest.raises(TransactionParseError):
        parse_transaction("coffee notanumber")


def test_parse_transaction_non_positive_amount():
    with pytest.raises(TransactionParseError):
        parse_transaction("coffee -1")


def test_parse_transaction_too_many_decimals():
    with pytest.raises(TransactionParseError):
        parse_transaction("coffee 6.999")

