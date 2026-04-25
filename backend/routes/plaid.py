from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models import PlaidItem
from backend.services.plaid_service import (
    PlaidApiError,
    PlaidConfigError,
    create_link_token,
    exchange_public_token,
    sync_plaid_item_transactions,
    upsert_plaid_item,
)
from backend.services.user_service import get_or_create_user_by_phone

router = APIRouter(prefix="/plaid", tags=["plaid"])


class LinkTokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str = Field(min_length=1)


class ExchangeTokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str = Field(min_length=1)
    public_token: str = Field(min_length=1)
    institution_id: str | None = None
    institution_name: str | None = None


class SyncPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str = Field(min_length=1)


class PlaidWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    webhook_type: str | None = None
    webhook_code: str | None = None
    item_id: str | None = None


def _plaid_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PlaidConfigError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


@router.post("/link-token")
def plaid_link_token(payload: LinkTokenPayload, db: Session = Depends(get_db)) -> dict[str, str]:
    user = get_or_create_user_by_phone(db, payload.phone_number)
    try:
        link_token = create_link_token(user)
    except (PlaidApiError, PlaidConfigError) as exc:
        raise _plaid_http_error(exc) from exc
    return {"link_token": link_token}


@router.post("/exchange-public-token")
def plaid_exchange_public_token(
    payload: ExchangeTokenPayload,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = get_or_create_user_by_phone(db, payload.phone_number)
    try:
        token_data = exchange_public_token(payload.public_token)
        plaid_item = upsert_plaid_item(
            db=db,
            user_id=user.id,
            access_token=token_data["access_token"],
            item_id=token_data["item_id"],
            institution_id=payload.institution_id,
            institution_name=payload.institution_name,
        )
        sync_result = sync_plaid_item_transactions(db, plaid_item)
    except (PlaidApiError, PlaidConfigError) as exc:
        raise _plaid_http_error(exc) from exc

    return {
        "user_id": user.id,
        "plaid_item_id": plaid_item.plaid_item_id,
        "institution_name": plaid_item.institution_name,
        "sync": sync_result,
    }


@router.post("/sync")
def plaid_sync(payload: SyncPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    user = get_or_create_user_by_phone(db, payload.phone_number)
    plaid_items = db.execute(
        select(PlaidItem).where(PlaidItem.user_id == user.id).order_by(PlaidItem.id.asc())
    ).scalars().all()
    if not plaid_items:
        raise HTTPException(status_code=404, detail="No Plaid connection found for this user.")

    total = {"added": 0, "modified": 0, "removed": 0}
    try:
        for plaid_item in plaid_items:
            result = sync_plaid_item_transactions(db, plaid_item)
            for key in total:
                total[key] += result[key]
    except (PlaidApiError, PlaidConfigError) as exc:
        raise _plaid_http_error(exc) from exc

    return {"user_id": user.id, "sync": total}


@router.post("/webhook")
def plaid_webhook(payload: PlaidWebhookPayload, db: Session = Depends(get_db)) -> dict[str, object]:
    if payload.webhook_type != "TRANSACTIONS" or payload.webhook_code != "SYNC_UPDATES_AVAILABLE":
        return {"ok": True, "synced": False}

    if not payload.item_id:
        raise HTTPException(status_code=400, detail="Plaid webhook missing item_id.")

    plaid_item = db.execute(
        select(PlaidItem).where(PlaidItem.plaid_item_id == payload.item_id)
    ).scalar_one_or_none()
    if plaid_item is None:
        return {"ok": True, "synced": False}

    try:
        sync_result = sync_plaid_item_transactions(db, plaid_item)
    except (PlaidApiError, PlaidConfigError) as exc:
        raise _plaid_http_error(exc) from exc

    return {"ok": True, "synced": True, "sync": sync_result}
