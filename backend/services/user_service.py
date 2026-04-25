from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


def get_user_by_phone(db: Session, phone_number: str) -> User | None:
    normalized_phone = phone_number.strip()
    if not normalized_phone:
        return None

    return db.execute(
        select(User).where(User.phone_number == normalized_phone)
    ).scalar_one_or_none()


def get_or_create_user_by_phone(db: Session, phone_number: str) -> User:
    normalized_phone = phone_number.strip()
    if not normalized_phone:
        raise ValueError("Phone number is required.")

    existing = get_user_by_phone(db, normalized_phone)
    if existing:
        return existing

    user = User(phone_number=normalized_phone)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.execute(select(User).where(User.phone_number == normalized_phone)).scalar_one()
        return existing

    db.refresh(user)
    return user
