from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models import Goal, Transaction, User
from backend.services.user_service import get_or_create_user_by_phone, get_user_by_id

router = APIRouter(tags=["dashboard"])


class TransactionResponse(BaseModel):
    id: int
    category: str
    amount: float
    occurred_at: str


class GoalResponse(BaseModel):
    id: int
    name: str
    target_amount: float
    current_amount: float
    remaining_amount: float
    is_active: bool


class GoalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    target_amount: Decimal | None = Field(default=None, gt=0)
    current_amount: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


def _resolve_user(
    db: Session,
    user_id: int | None,
    phone_number: str | None,
) -> User:
    if user_id is None and not phone_number:
        raise HTTPException(status_code=400, detail="Provide user_id or phone_number.")

    user = None
    if user_id is not None:
        user = get_user_by_id(db, user_id)
    elif phone_number is not None:
        user = get_or_create_user_by_phone(db, phone_number)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def _goal_to_response(goal: Goal | None) -> GoalResponse | None:
    if goal is None:
        return None

    target_amount = round(float(goal.target_amount), 2)
    current_amount = round(float(goal.current_amount), 2)
    remaining_amount = round(max(target_amount - current_amount, 0.0), 2)
    return GoalResponse(
        id=goal.id,
        name=goal.name,
        target_amount=target_amount,
        current_amount=current_amount,
        remaining_amount=remaining_amount,
        is_active=goal.is_active,
    )


@router.get("/transactions")
def get_transactions(
    user_id: int | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = _resolve_user(db, user_id, phone_number)
    transactions = db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
        .limit(limit)
    ).scalars().all()

    return {
        "user_id": user.id,
        "transactions": [
            TransactionResponse(
                id=transaction.id,
                category=transaction.category,
                amount=round(float(transaction.amount), 2),
                occurred_at=transaction.occurred_at.isoformat(),
            ).model_dump()
            for transaction in transactions
        ],
    }


@router.get("/goals")
def get_goals(
    user_id: int | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = _resolve_user(db, user_id, phone_number)
    active_goal = db.execute(
        select(Goal)
        .where(Goal.user_id == user.id, Goal.is_active.is_(True))
        .order_by(Goal.updated_at.desc(), Goal.id.desc())
    ).scalars().first()

    return {
        "user_id": user.id,
        "goal": _goal_to_response(active_goal).model_dump() if active_goal is not None else None,
    }


@router.patch("/goals")
def patch_goals(
    payload: GoalPayload,
    user_id: int | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    user = _resolve_user(db, user_id, phone_number)
    active_goal = db.execute(
        select(Goal)
        .where(Goal.user_id == user.id, Goal.is_active.is_(True))
        .order_by(Goal.updated_at.desc(), Goal.id.desc())
    ).scalars().first()

    if active_goal is None:
        if payload.name is None or payload.target_amount is None:
            raise HTTPException(
                status_code=400,
                detail="name and target_amount are required when creating a goal.",
            )
        active_goal = Goal(
            user_id=user.id,
            name=payload.name.strip(),
            target_amount=payload.target_amount,
            current_amount=payload.current_amount or Decimal("0"),
            is_active=payload.is_active if payload.is_active is not None else True,
        )
        db.add(active_goal)
    else:
        if payload.name is not None:
            active_goal.name = payload.name.strip()
        if payload.target_amount is not None:
            active_goal.target_amount = payload.target_amount
        if payload.current_amount is not None:
            active_goal.current_amount = payload.current_amount
        if payload.is_active is not None:
            active_goal.is_active = payload.is_active

    db.commit()
    db.refresh(active_goal)

    return {
        "user_id": user.id,
        "goal": _goal_to_response(active_goal).model_dump(),
    }
