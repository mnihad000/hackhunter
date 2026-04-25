from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.core.config import Environment, collect_config_errors, get_settings
from backend.core.exceptions import ConfigValidationError
from backend.routes.dashboard import router as dashboard_router
from backend.routes.predict import router as predict_router
from backend.routes.sms import router as sms_router
from backend.routes.system import router as system_router
from backend.services.scheduler import run_scheduler_forever, should_start_scheduler

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        debug=settings.app.debug,
    )
    app.include_router(system_router)
    app.include_router(sms_router)
    app.include_router(predict_router)
    app.include_router(dashboard_router)

    @app.exception_handler(ConfigValidationError)
    async def config_error_handler(_, exc: ConfigValidationError) -> JSONResponse:
        return JSONResponse(status_code=500, content=exc.as_dict())

    @app.on_event("startup")
    def validate_config_on_startup() -> None:
        config_errors = collect_config_errors(settings, strict=settings.app.env == Environment.prod)
        if config_errors and settings.app.env != Environment.test:
            raise ConfigValidationError(config_errors)
        if config_errors:
            logger.warning("App started in test mode with config issues: %s", config_errors)

    @app.on_event("startup")
    async def start_scheduler_on_startup() -> None:
        if should_start_scheduler():
            app.state.scheduler_task = asyncio.create_task(run_scheduler_forever())

    @app.on_event("shutdown")
    async def stop_scheduler_on_shutdown() -> None:
        scheduler_task = getattr(app.state, "scheduler_task", None)
        if scheduler_task is not None:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled.")

    return app


app = create_app()
