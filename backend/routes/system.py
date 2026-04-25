from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.core.config import Environment, collect_config_errors, get_settings
from backend.db.session import check_required_tables, ping_database

router = APIRouter(tags=["system"])
REQUIRED_TABLES = {"users", "transactions", "goals", "feedback", "nudge_events", "plaid_items"}


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "piggybank-backend"}


@router.get("/readyz", response_model=None)
def readyz() -> JSONResponse | dict[str, object]:
    settings = get_settings()
    errors = collect_config_errors(settings, strict=settings.app.env == Environment.prod)

    db_status = "skipped"
    schema_status = "skipped"
    if settings.database.url:
        db_ok, db_error = ping_database(settings.database.url)
        if db_ok:
            db_status = "ok"
            schema_ok, missing_tables = check_required_tables(REQUIRED_TABLES, settings.database.url)
            if schema_ok:
                schema_status = "ok"
            else:
                schema_status = "error"
                errors.append(
                    "database schema missing required tables: "
                    + ", ".join(missing_tables)
                )
        else:
            db_status = "error"
            errors.append(f"database ping failed: {db_error}")
            schema_status = "skipped"
    else:
        db_status = "missing_config"
        schema_status = "missing_config"

    if errors:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {"config": "error", "database": db_status, "schema": schema_status},
                "errors": errors,
            },
        )

    return {
        "status": "ready",
        "checks": {"config": "ok", "database": db_status, "schema": schema_status},
    }
