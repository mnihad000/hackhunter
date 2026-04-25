from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class TransactionParseError(ValueError):
    """Raised when incoming transaction text is malformed."""


@dataclass(frozen=True)
class ParsedTransaction:
    category: str
    amount: Decimal


def _normalize_category(raw_category: str) -> str:
    normalized = " ".join(raw_category.strip().lower().split())
    if not normalized:
        raise TransactionParseError("Category is required.")
    if len(normalized) > 64:
        raise TransactionParseError("Category is too long.")
    return normalized


def _parse_amount(raw_amount: str) -> Decimal:
    cleaned = raw_amount.strip()
    if cleaned.startswith("$"):
        cleaned = cleaned[1:].strip()
    if not cleaned:
        raise TransactionParseError("Amount is required.")

    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise TransactionParseError("Amount must be numeric.") from exc

    if amount <= 0:
        raise TransactionParseError("Amount must be greater than zero.")

    decimal_places = -amount.as_tuple().exponent if amount.as_tuple().exponent < 0 else 0
    if decimal_places > 2:
        raise TransactionParseError("Amount can have at most 2 decimal places.")

    return amount.quantize(Decimal("0.01"))


def parse_transaction(text: str) -> ParsedTransaction:
    normalized_text = text.strip()
    if not normalized_text:
        raise TransactionParseError("Transaction text is required.")

    parts = normalized_text.split()
    if len(parts) < 2:
        raise TransactionParseError("Use format: <category> <amount>.")

    amount_raw = parts[-1]
    category_raw = " ".join(parts[:-1])

    category = _normalize_category(category_raw)
    amount = _parse_amount(amount_raw)
    return ParsedTransaction(category=category, amount=amount)

