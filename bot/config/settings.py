"""Configuration and settings module.

All configuration is loaded from environment variables (``.env``). There is no
secondary ``config.json`` anymore — everything needed to run the bot lives in
``.env`` so the launch is a single, predictable source of truth.
"""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core / Telegram ---
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: str = Field(..., alias="ADMIN_IDS")
    channel_id: int = Field(..., alias="CHANNEL_ID")
    join_url: str = Field(..., alias="JOIN_URL")

    # --- Infrastructure ---
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    # Namespace for aiogram FSM keys so multiple bots can share one Redis safely.
    redis_fsm_prefix: str = Field(default="fsm", alias="REDIS_FSM_PREFIX")

    # Database connection pool (kept modest so several bots can share one server).
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")

    # --- Behaviour ---
    # NOTE: display timezone is fixed to Moscow (MSK, GMT+3) in bot.utils.datetimes
    # and is intentionally NOT configurable.
    broadcast_rps: int = Field(default=20, alias="BROADCAST_RPS")
    announce_rps: int = Field(default=20, alias="ANNOUNCE_RPS")
    max_retries: int = Field(default=5, alias="MAX_RETRIES")

    # --- Google Sheets (optional) ---
    sheets_sync_enabled: bool = Field(default=False, alias="SHEETS_SYNC_ENABLED")
    google_credentials_path: str | None = Field(default=None, alias="GOOGLE_CREDENTIALS_PATH")
    spreadsheet_id: str | None = Field(default=None, alias="SPREADSHEET_ID")

    # --- Logging / observability ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _normalize_admin_ids(cls, v: Any) -> str:
        """Allow admin_ids to be passed as int or comma-separated string."""
        return v if isinstance(v, str) else str(v)

    def get_admin_ids(self) -> list[int]:
        """Parse the comma-separated admin id list into ints."""
        return [int(part.strip()) for part in self.admin_ids.split(",") if part.strip()]

    def is_admin(self, user_id: int) -> bool:
        """Check whether ``user_id`` is configured as an admin."""
        return user_id in self.get_admin_ids()


# Global settings instance (initialised once at startup).
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the process-wide settings instance, creating it on first use."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def init_settings(env_file: str | None = None) -> Settings:
    """(Re)initialise settings, optionally from a custom env file."""
    global _settings
    _settings = Settings(_env_file=env_file) if env_file else Settings()
    return _settings
