from __future__ import annotations

import datetime as dt
from decimal import Decimal
import logging
import re
from typing import Any

import httpx
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from backend.core.config import get_settings
from backend.models import PlaidItem, Transaction, User
from backend.services.user_service import get_or_create_user_by_phone, get_user_by_phone

logger = logging.getLogger(__name__)
UTC = dt.timezone.utc
PLAID_BASE_URLS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}


class PlaidServiceError(Exception):
    def __init__(self, detail: str, *, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


PLAID_REQUIRED_COLUMNS = {
    "transactions": {"source", "plaid_transaction_id", "merchant_name"},
    "plaid_items": {"plaid_item_id", "access_token", "institution_name", "sync_cursor", "status", "last_synced_at"},
}


def _ensure_plaid_schema(db: Session) -> None:
    inspector = inspect(db.get_bind())
    available_tables = set(inspector.get_table_names())
    missing_details: list[str] = []

    for table_name, expected_columns in PLAID_REQUIRED_COLUMNS.items():
        if table_name not in available_tables:
            missing_details.append(f"{table_name}(table)")
            continue

        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = sorted(expected_columns.difference(actual_columns))
        if missing_columns:
            missing_details.append(f"{table_name}({', '.join(missing_columns)})")

    if missing_details:
        raise PlaidServiceError(
            "Plaid schema is out of date. Run `python -m alembic upgrade head` to add: "
            + "; ".join(missing_details),
            status_code=503,
        )


def _get_plaid_base_url() -> str:
    settings = get_settings()
    return PLAID_BASE_URLS[settings.plaid.env]


def _request_plaid(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.plaid.client_id or not settings.plaid.secret:
        raise PlaidServiceError("Plaid is not configured.", status_code=500)

    request_payload = {
        "client_id": settings.plaid.client_id,
        "secret": settings.plaid.secret,
        **payload,
    }
    url = f"{_get_plaid_base_url()}{path}"

    try:
        with httpx.Client(timeout=settings.plaid.timeout_seconds) as client:
            response = client.post(url, json=request_payload)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        try:
            payload = exc.response.json()
        except ValueError:
            payload = {}
        error_message = payload.get("error_message") or exc.response.text or str(exc)
        raise PlaidServiceError(
            f"Plaid request failed: {error_message}",
            status_code=502,
        ) from exc
    except httpx.HTTPError as exc:
        raise PlaidServiceError(f"Plaid request failed: {exc}", status_code=502) from exc

    return response.json()


def _normalize_category(transaction_payload: dict[str, Any]) -> str:
    personal_finance_category = transaction_payload.get("personal_finance_category") or {}
    primary = personal_finance_category.get("primary")
    if isinstance(primary, str) and primary.strip():
        value = primary
    else:
        categories = transaction_payload.get("category") or []
        value = categories[0] if categories else transaction_payload.get("name") or "uncategorized"
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return normalized or "uncategorized"


def _parse_transaction_time(transaction_payload: dict[str, Any]) -> dt.datetime:
    for key in ("authorized_datetime", "datetime"):
        value = transaction_payload.get(key)
        if isinstance(value, str) and value:
            return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

    value = transaction_payload.get("date")
    if isinstance(value, str) and value:
        parsed_date = dt.date.fromisoformat(value)
        return dt.datetime(
            parsed_date.year,
            parsed_date.month,
            parsed_date.day,
            12,
            0,
            tzinfo=UTC,
        )

    return dt.datetime.now(tz=UTC)


def _upsert_plaid_transaction(
    db: Session,
    *,
    user_id: int,
    transaction_payload: dict[str, Any],
) -> bool:
    plaid_transaction_id = transaction_payload.get("transaction_id")
    if not isinstance(plaid_transaction_id, str) or not plaid_transaction_id:
        return False

    amount = Decimal(str(transaction_payload.get("amount", "0")))
    category = _normalize_category(transaction_payload)
    merchant_name = transaction_payload.get("merchant_name") or transaction_payload.get("name")
    occurred_at = _parse_transaction_time(transaction_payload)

    existing = db.execute(
        select(Transaction).where(Transaction.plaid_transaction_id == plaid_transaction_id)
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            Transaction(
                user_id=user_id,
                category=category,
                source="plaid",
                plaid_transaction_id=plaid_transaction_id,
                merchant_name=str(merchant_name).strip() if merchant_name else None,
                amount=amount,
                occurred_at=occurred_at,
            )
        )
        return True

    existing.category = category
    existing.source = "plaid"
    existing.merchant_name = str(merchant_name).strip() if merchant_name else None
    existing.amount = amount
    existing.occurred_at = occurred_at
    return False


def _remove_plaid_transactions(db: Session, removed_payloads: list[dict[str, Any]]) -> int:
    removed_count = 0
    for removed_payload in removed_payloads:
        transaction_id = removed_payload.get("transaction_id")
        if not isinstance(transaction_id, str) or not transaction_id:
            continue

        existing = db.execute(
            select(Transaction).where(Transaction.plaid_transaction_id == transaction_id)
        ).scalar_one_or_none()
        if existing is None:
            continue

        db.delete(existing)
        removed_count += 1
    return removed_count


def _import_transactions_window(db: Session, *, access_token: str, user_id: int) -> int:
    settings = get_settings()
    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(days=settings.plaid.transactions_days_requested)

    imported_count = 0
    offset = 0
    page_size = 100
    while True:
        response_payload = _request_plaid(
            "/transactions/get",
            {
                "access_token": access_token,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "options": {"count": page_size, "offset": offset},
            },
        )
        transactions = response_payload.get("transactions") or []
        imported_count += sum(
            1
            for transaction_payload in transactions
            if _upsert_plaid_transaction(
                db,
                user_id=user_id,
                transaction_payload=transaction_payload,
            )
        )
        offset += len(transactions)
        if offset >= int(response_payload.get("total_transactions", 0)):
            break

    return imported_count


def _sync_plaid_item(db: Session, plaid_item: PlaidItem) -> dict[str, int]:
    cursor = plaid_item.sync_cursor
    imported_count = 0
    removed_count = 0

    while True:
        payload: dict[str, Any] = {"access_token": plaid_item.access_token}
        if cursor:
            payload["cursor"] = cursor

        response_payload = _request_plaid("/transactions/sync", payload)
        added = response_payload.get("added") or []
        modified = response_payload.get("modified") or []
        removed = response_payload.get("removed") or []

        imported_count += sum(
            1
            for transaction_payload in [*added, *modified]
            if _upsert_plaid_transaction(
                db,
                user_id=plaid_item.user_id,
                transaction_payload=transaction_payload,
            )
        )
        removed_count += _remove_plaid_transactions(db, removed)

        cursor = response_payload.get("next_cursor") or cursor
        if not response_payload.get("has_more"):
            break

    plaid_item.sync_cursor = cursor
    plaid_item.last_synced_at = dt.datetime.now(tz=UTC)
    plaid_item.status = "linked"
    db.commit()
    return {"imported_count": imported_count, "removed_count": removed_count}


def _get_existing_plaid_item(db: Session, *, plaid_item_id: str) -> PlaidItem | None:
    return db.execute(
        select(PlaidItem).where(PlaidItem.plaid_item_id == plaid_item_id)
    ).scalar_one_or_none()


def create_link_token(db: Session, phone_number: str) -> dict[str, Any]:
    settings = get_settings()
    _ensure_plaid_schema(db)
    user = get_or_create_user_by_phone(db, phone_number)
    response_payload = _request_plaid(
        "/link/token/create",
        {
            "client_name": settings.app.name,
            "country_codes": ["US"],
            "language": "en",
            "products": ["transactions"],
            "user": {"client_user_id": str(user.id)},
        },
    )
    return {
        "user_id": user.id,
        "link_token": response_payload["link_token"],
        "expiration": response_payload.get("expiration"),
    }


def exchange_public_token(
    db: Session,
    *,
    phone_number: str,
    public_token: str,
    institution_name: str | None = None,
) -> dict[str, Any]:
    _ensure_plaid_schema(db)
    user = get_or_create_user_by_phone(db, phone_number)
    response_payload = _request_plaid(
        "/item/public_token/exchange",
        {"public_token": public_token},
    )

    plaid_item_id = response_payload["item_id"]
    access_token = response_payload["access_token"]
    plaid_item = _get_existing_plaid_item(db, plaid_item_id=plaid_item_id)
    if plaid_item is None:
        plaid_item = PlaidItem(
            user_id=user.id,
            plaid_item_id=plaid_item_id,
            access_token=access_token,
            institution_name=institution_name.strip() if institution_name else None,
            status="linked",
        )
        db.add(plaid_item)
    else:
        plaid_item.user_id = user.id
        plaid_item.access_token = access_token
        if institution_name:
            plaid_item.institution_name = institution_name.strip()
        plaid_item.status = "linked"

    imported_count = _import_transactions_window(db, access_token=access_token, user_id=user.id)
    plaid_item.last_synced_at = dt.datetime.now(tz=UTC)
    db.commit()
    db.refresh(plaid_item)
    return {
        "user_id": user.id,
        "plaid_item_id": plaid_item.plaid_item_id,
        "institution_name": plaid_item.institution_name,
        "imported_count": imported_count,
    }


def sync_user_transactions(db: Session, *, phone_number: str) -> dict[str, Any]:
    _ensure_plaid_schema(db)
    user = get_user_by_phone(db, phone_number)
    if user is None:
        raise PlaidServiceError("User not found.", status_code=404)

    plaid_items = db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user.id).order_by(PlaidItem.id.asc())
    ).scalars().all()
    if not plaid_items:
        raise PlaidServiceError("No Plaid account is linked for this phone number.", status_code=404)

    imported_count = 0
    removed_count = 0
    for plaid_item in plaid_items:
        result = _sync_plaid_item(db, plaid_item)
        imported_count += result["imported_count"]
        removed_count += result["removed_count"]

    return {
        "user_id": user.id,
        "linked_items": len(plaid_items),
        "imported_count": imported_count,
        "removed_count": removed_count,
    }


def handle_plaid_webhook(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_plaid_schema(db)
    plaid_item_id = payload.get("item_id")
    if not isinstance(plaid_item_id, str) or not plaid_item_id:
        return {"status": "ignored", "reason": "missing_item_id"}

    plaid_item = _get_existing_plaid_item(db, plaid_item_id=plaid_item_id)
    if plaid_item is None:
        return {"status": "ignored", "reason": "unknown_item"}

    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")
    if webhook_type == "TRANSACTIONS":
        result = _sync_plaid_item(db, plaid_item)
        return {
            "status": "synced",
            "webhook_type": webhook_type,
            "webhook_code": webhook_code,
            "plaid_item_id": plaid_item_id,
            **result,
        }

    logger.info("Ignoring Plaid webhook type=%s code=%s item=%s", webhook_type, webhook_code, plaid_item_id)
    return {
        "status": "ignored",
        "webhook_type": webhook_type,
        "webhook_code": webhook_code,
        "plaid_item_id": plaid_item_id,
    }
