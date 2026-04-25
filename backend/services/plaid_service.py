from __future__ import annotations

import datetime as dt
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models import PlaidItem, Transaction, User

PLAID_BASE_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


class PlaidConfigError(RuntimeError):
    """Raised when Plaid is not configured for API calls."""


class PlaidApiError(RuntimeError):
    """Raised when Plaid returns an error response."""


def _plaid_base_url() -> str:
    settings = get_settings()
    return PLAID_BASE_URLS.get(settings.plaid.env, PLAID_BASE_URLS["sandbox"])


def _post_plaid(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.plaid.client_id or not settings.plaid.secret:
        raise PlaidConfigError("Plaid Sandbox keys are not configured.")

    request_payload = {
        **payload,
        "client_id": settings.plaid.client_id,
        "secret": settings.plaid.secret,
    }
    response = httpx.post(
        f"{_plaid_base_url()}{endpoint}",
        json=request_payload,
        timeout=20,
    )
    if response.status_code >= 400:
        try:
            body = response.json()
            message = body.get("error_message") or body.get("error_code") or response.text
        except ValueError:
            message = response.text
        raise PlaidApiError(f"Plaid {endpoint} failed: {message}")
    return response.json()


def create_link_token(user: User) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "user": {"client_user_id": str(user.id)},
        "client_name": settings.app.name,
        "products": ["transactions"],
        "country_codes": ["US"],
        "language": "en",
        "transactions": {
            "days_requested": settings.plaid.transactions_days_requested,
        },
    }
    if settings.plaid.webhook_url:
        payload["webhook"] = settings.plaid.webhook_url

    response = _post_plaid("/link/token/create", payload)
    return str(response["link_token"])


def exchange_public_token(public_token: str) -> dict[str, str]:
    response = _post_plaid("/item/public_token/exchange", {"public_token": public_token})
    return {
        "access_token": str(response["access_token"]),
        "item_id": str(response["item_id"]),
    }


def upsert_plaid_item(
    db: Session,
    user_id: int,
    access_token: str,
    item_id: str,
    institution_id: str | None = None,
    institution_name: str | None = None,
) -> PlaidItem:
    plaid_item = db.execute(
        select(PlaidItem).where(PlaidItem.plaid_item_id == item_id)
    ).scalar_one_or_none()
    if plaid_item is None:
        plaid_item = PlaidItem(
            user_id=user_id,
            plaid_item_id=item_id,
            access_token=access_token,
            institution_id=institution_id,
            institution_name=institution_name,
        )
        db.add(plaid_item)
    else:
        plaid_item.user_id = user_id
        plaid_item.access_token = access_token
        plaid_item.institution_id = institution_id or plaid_item.institution_id
        plaid_item.institution_name = institution_name or plaid_item.institution_name

    db.commit()
    db.refresh(plaid_item)
    return plaid_item


def _parse_plaid_date(transaction: dict[str, Any]) -> dt.datetime:
    raw_datetime = transaction.get("datetime")
    if raw_datetime:
        parsed = dt.datetime.fromisoformat(str(raw_datetime).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)

    raw_date = transaction.get("date")
    if raw_date:
        return dt.datetime.combine(
            dt.date.fromisoformat(str(raw_date)),
            dt.time(hour=12, tzinfo=dt.timezone.utc),
        )

    return dt.datetime.now(dt.timezone.utc)


def _normalize_plaid_category(transaction: dict[str, Any]) -> str:
    personal_category = transaction.get("personal_finance_category") or {}
    primary = personal_category.get("primary") if isinstance(personal_category, dict) else None
    if isinstance(primary, str) and primary.strip():
        mapping = {
            "FOOD_AND_DRINK": "food",
            "TRANSPORTATION": "transportation",
            "GENERAL_MERCHANDISE": "shopping",
            "ENTERTAINMENT": "entertainment",
            "TRAVEL": "travel",
            "RENT_AND_UTILITIES": "bills",
        }
        return mapping.get(primary, primary.lower().replace("_", " "))

    categories = transaction.get("category")
    if isinstance(categories, list) and categories:
        return str(categories[0]).strip().lower()[:64] or "uncategorized"
    return "uncategorized"


def _decimal_amount(value: Any) -> Decimal | None:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return amount if amount > 0 else None


def _upsert_transaction_from_plaid(
    db: Session,
    user_id: int,
    plaid_transaction: dict[str, Any],
) -> bool:
    transaction_id = plaid_transaction.get("transaction_id")
    amount = _decimal_amount(plaid_transaction.get("amount"))
    if not transaction_id or amount is None:
        return False

    existing = db.execute(
        select(Transaction).where(
            Transaction.source == "plaid",
            Transaction.external_id == str(transaction_id),
        )
    ).scalar_one_or_none()

    merchant_name = plaid_transaction.get("merchant_name") or plaid_transaction.get("name")
    values = {
        "user_id": user_id,
        "category": _normalize_plaid_category(plaid_transaction),
        "merchant_name": str(merchant_name)[:255] if merchant_name else None,
        "amount": amount,
        "occurred_at": _parse_plaid_date(plaid_transaction),
        "source": "plaid",
        "external_id": str(transaction_id),
        "pending": bool(plaid_transaction.get("pending", False)),
    }

    if existing is None:
        db.add(Transaction(**values))
        return True

    for key, value in values.items():
        setattr(existing, key, value)
    return False


def sync_plaid_item_transactions(db: Session, plaid_item: PlaidItem) -> dict[str, int]:
    added_count = 0
    modified_count = 0
    removed_count = 0
    cursor = plaid_item.sync_cursor

    while True:
        payload: dict[str, Any] = {"access_token": plaid_item.access_token, "count": 100}
        if cursor:
            payload["cursor"] = cursor
        response = _post_plaid("/transactions/sync", payload)

        for transaction in response.get("added", []):
            if _upsert_transaction_from_plaid(db, plaid_item.user_id, transaction):
                added_count += 1

        for transaction in response.get("modified", []):
            _upsert_transaction_from_plaid(db, plaid_item.user_id, transaction)
            modified_count += 1

        for removed in response.get("removed", []):
            transaction_id = removed.get("transaction_id")
            if not transaction_id:
                continue
            existing = db.execute(
                select(Transaction).where(
                    Transaction.source == "plaid",
                    Transaction.external_id == str(transaction_id),
                )
            ).scalar_one_or_none()
            if existing is not None:
                db.delete(existing)
                removed_count += 1

        cursor = response.get("next_cursor")
        if not response.get("has_more"):
            break

    plaid_item.sync_cursor = str(cursor) if cursor else plaid_item.sync_cursor
    db.commit()
    return {"added": added_count, "modified": modified_count, "removed": removed_count}
