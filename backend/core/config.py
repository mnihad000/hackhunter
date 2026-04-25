from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.exceptions import ConfigValidationError


class Environment(str, Enum):
    local = "local"
    test = "test"
    prod = "prod"


class AppConfig(BaseModel):
    name: str = "PiggyBank Backend"
    version: str = "0.1.0"
    env: Environment = Environment.local
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseConfig(BaseModel):
    url: str | None = None
    echo: bool = False


class TwilioConfig(BaseModel):
    account_sid: str | None = None
    auth_token: str | None = None
    phone_number: str | None = None
    validate_signature: bool = True


class GeminiConfig(BaseModel):
    api_key: str | None = None
    model: str = "gemini-2.5-flash"
    timeout_seconds: int = 10


class PlaidConfig(BaseModel):
    client_id: str | None = None
    secret: str | None = None
    env: str = "sandbox"
    webhook_url: str | None = None
    transactions_days_requested: int = 180


class SchedulerConfig(BaseModel):
    enabled: bool = True
    interval_seconds: int = 60


class PredictionConfig(BaseModel):
    nudge_probability_threshold: float = 0.65
    nudge_cooldown_minutes: int = 120
    lookback_days: int = 90
    min_transactions_per_category: int = 3
    recency_half_life_days: int = 14
    window_floor_minutes: int = 30
    window_cap_minutes: int = 180
    max_candidates_per_user: int = 1


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    twilio: TwilioConfig = Field(default_factory=TwilioConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    plaid: PlaidConfig = Field(default_factory=PlaidConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    prediction: PredictionConfig = Field(default_factory=PredictionConfig)


def collect_config_errors(settings: Settings, *, strict: bool = False) -> list[str]:
    errors: list[str] = []

    if not settings.database.url:
        errors.append("DATABASE__URL is required.")

    if settings.app.env != Environment.test:
        if not settings.twilio.account_sid:
            errors.append("TWILIO__ACCOUNT_SID is required outside test mode.")
        if not settings.twilio.auth_token:
            errors.append("TWILIO__AUTH_TOKEN is required outside test mode.")
        if not settings.twilio.phone_number:
            errors.append("TWILIO__PHONE_NUMBER is required outside test mode.")
        if not settings.gemini.api_key:
            errors.append("GEMINI__API_KEY is required outside test mode.")

    if settings.scheduler.interval_seconds <= 0:
        errors.append("SCHEDULER__INTERVAL_SECONDS must be greater than 0.")

    if settings.gemini.timeout_seconds <= 0:
        errors.append("GEMINI__TIMEOUT_SECONDS must be greater than 0.")

    if settings.plaid.env not in {"sandbox", "development", "production"}:
        errors.append("PLAID__ENV must be sandbox, development, or production.")

    if (settings.plaid.client_id and not settings.plaid.secret) or (
        settings.plaid.secret and not settings.plaid.client_id
    ):
        errors.append("PLAID__CLIENT_ID and PLAID__SECRET must be configured together.")

    if not 1 <= settings.plaid.transactions_days_requested <= 730:
        errors.append("PLAID__TRANSACTIONS_DAYS_REQUESTED must be between 1 and 730.")

    if not 0 <= settings.prediction.nudge_probability_threshold <= 1:
        errors.append("PREDICTION__NUDGE_PROBABILITY_THRESHOLD must be between 0 and 1.")

    if settings.prediction.nudge_cooldown_minutes < 0:
        errors.append("PREDICTION__NUDGE_COOLDOWN_MINUTES cannot be negative.")

    if settings.prediction.lookback_days <= 0:
        errors.append("PREDICTION__LOOKBACK_DAYS must be greater than 0.")

    if settings.prediction.min_transactions_per_category < 3:
        errors.append("PREDICTION__MIN_TRANSACTIONS_PER_CATEGORY must be at least 3.")

    if settings.prediction.recency_half_life_days <= 0:
        errors.append("PREDICTION__RECENCY_HALF_LIFE_DAYS must be greater than 0.")

    if settings.prediction.window_floor_minutes <= 0:
        errors.append("PREDICTION__WINDOW_FLOOR_MINUTES must be greater than 0.")

    if settings.prediction.window_cap_minutes < settings.prediction.window_floor_minutes:
        errors.append(
            "PREDICTION__WINDOW_CAP_MINUTES must be greater than or equal to "
            "PREDICTION__WINDOW_FLOOR_MINUTES."
        )

    if settings.prediction.max_candidates_per_user <= 0:
        errors.append("PREDICTION__MAX_CANDIDATES_PER_USER must be greater than 0.")

    if strict:
        if settings.app.env == Environment.prod and settings.app.debug:
            errors.append("APP__DEBUG must be false when APP__ENV=prod.")
        if settings.app.env == Environment.prod and not settings.twilio.validate_signature:
            errors.append("TWILIO__VALIDATE_SIGNATURE must be true when APP__ENV=prod.")

    return errors


def validate_settings_or_raise(settings: Settings, *, strict: bool = False) -> None:
    errors = collect_config_errors(settings, strict=strict)
    if errors:
        raise ConfigValidationError(errors)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
