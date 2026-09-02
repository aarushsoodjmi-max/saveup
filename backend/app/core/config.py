from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "SaveUp API"
    app_version: str = "1.0.0"
    environment: str = "development"  # development | testing | production
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # --- Redis ---
    redis_url: str

    # --- JWT ---
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION_super_secret_key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # --- OTP ---
    otp_length: int = 6
    otp_expire_seconds: int = 300  # 5 minutes
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 60
    otp_hash_secret: str = "CHANGE_ME_OTP_PEPPER"
    # Only relevant outside production: echoes the generated OTP back in
    # the send-otp response so the API can be exercised without a real
    # SMS provider.
    otp_debug_expose: bool = True

    # --- Rate limiting (Redis token counters) ---
    rate_limit_otp_per_hour: int = 5
    rate_limit_login_per_hour: int = 10
    rate_limit_default_per_minute: int = 60

    # --- Idempotency ---
    idempotency_key_ttl_seconds: int = 86400  # 24 hours

    # --- Ledger retry (transient MySQL write-conflict recovery) ---
    # Applies to retryable DBAPI errors surfaced during a row-locked
    # ledger operation -- e.g. MySQL 1020 ("Record has changed since
    # last read"), 1213 (deadlock), 1205 (lock wait timeout). The whole
    # locked operation (re-acquire lock, re-check idempotency, re-apply)
    # is retried, never just the failing statement.
    ledger_retry_max_attempts: int = 3
    ledger_retry_base_backoff_seconds: float = 0.05

    # --- Mock payment provider ---
    payment_webhook_secret: str = "CHANGE_ME_PAYMENT_WEBHOOK_SECRET"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:8080"

    # --- Pagination ---
    default_page_size: int = 20
    max_page_size: int = 100

    # --- Logging ---
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("environment")
    @classmethod
    def _normalize_environment(cls, value: str) -> str:
        return value.strip().lower()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor.

    Using ``lru_cache`` means the ``.env`` file is only parsed once per
    process, while still allowing tests to override it after
    monkeypatching environment variables and calling
    ``get_settings.cache_clear()``.
    """
    return Settings()


# Module-level singleton used throughout the app. Prefer importing this
# directly (``from app.core.config import settings``) over instantiating
# ``Settings()`` again in individual modules.
settings = get_settings()
