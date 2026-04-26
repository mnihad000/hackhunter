from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.plaid import (
    PlaidServiceError,
    create_link_token,
    exchange_public_token,
    handle_plaid_webhook,
    sync_user_transactions,
)

router = APIRouter(prefix="/plaid", tags=["plaid"])


class PublicTokenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public_token: str = Field(min_length=1)
    institution_name: str | None = Field(default=None, min_length=1, max_length=120)


class PlaidWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    webhook_type: str | None = None
    webhook_code: str | None = None
    item_id: str | None = None


def _raise_http_error(exc: PlaidServiceError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/link-token")
def create_plaid_link_token(
    phone_number: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return create_link_token(db, phone_number.strip())
    except PlaidServiceError as exc:
        _raise_http_error(exc)


@router.post("/exchange-public-token")
def exchange_plaid_public_token(
    payload: PublicTokenPayload,
    phone_number: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return exchange_public_token(
            db,
            phone_number=phone_number.strip(),
            public_token=payload.public_token.strip(),
            institution_name=payload.institution_name,
        )
    except PlaidServiceError as exc:
        _raise_http_error(exc)


@router.post("/sync")
def sync_plaid_transactions(
    phone_number: str = Query(min_length=1),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return sync_user_transactions(db, phone_number=phone_number.strip())
    except PlaidServiceError as exc:
        _raise_http_error(exc)


@router.post("/webhook")
def receive_plaid_webhook(
    payload: PlaidWebhookPayload,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        return handle_plaid_webhook(db, payload.model_dump(exclude_none=True))
    except PlaidServiceError as exc:
        _raise_http_error(exc)
