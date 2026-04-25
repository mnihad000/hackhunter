from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.models import Transaction


def save_transaction(
    db: Session,
    user_id: int,
    category: str,
    amount: Decimal,
    occurred_at: dt.datetime | None = None,
) -> Transaction:
    transaction = Transaction(
        user_id=user_id,
        category=category,
        amount=amount,
        occurred_at=occurred_at or dt.datetime.utcnow(),
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

