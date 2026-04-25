from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.prediction import predict_for_user
from backend.services.user_service import get_user_by_id, get_user_by_phone

router = APIRouter(tags=["predict"])


@router.get("/predict")
def get_predictions(
    user_id: int | None = Query(default=None),
    phone_number: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if user_id is None and not phone_number:
        raise HTTPException(status_code=400, detail="Provide user_id or phone_number.")

    user = None
    if user_id is not None:
        user = get_user_by_id(db, user_id)
    elif phone_number is not None:
        user = get_user_by_phone(db, phone_number)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    predictions = predict_for_user(db, user.id)
    return {
        "user_id": user.id,
        "predictions": [prediction.model_dump(mode="json") for prediction in predictions],
    }
