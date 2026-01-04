"""Configuration and settings module using Pydantic Settings."""

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimits(BaseSettings):
    """Rate limiting configuration."""

    broadcast_rps: int = 20
    announce_rps: int = 20
    burst: int = 5
    max_retries: int = 5


class SheetsSyncConfig(BaseSettings):
    """Google Sheets synchronization configuration."""

    enabled: bool = False
    flush_sec: float = 1.0
    max_updates: int = 200
    max_appends: int = 200
    max_deletes: int = 200


class AdminPanelConfig(BaseSettings):
    """Admin panel UI configuration."""

    items_per_page: int = 10


class AppConfig(BaseSettings):
    """Application-wide configuration loaded from config.json."""

    timezone: str = "Europe/Moscow"
    join_url: str
    rate_limits: RateLimits = Field(default_factory=RateLimits)
    admin_panel: AdminPanelConfig = Field(default_factory=AdminPanelConfig)
    sheets_sync: SheetsSyncConfig = Field(default_factory=SheetsSyncConfig)

    @classmethod
    def load_from_file(cls, config_path: Path) -> "AppConfig":
        """Load configuration from JSON file."""
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


class Settings(BaseSettings):
    """Main settings class combining environment variables and config file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Bot configuration from .env
    bot_token: str = Field(..., alias="BOT_TOKEN")

    # Database configuration
    database_url: str = Field(..., alias="DATABASE_URL")

    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Admin configuration
    admin_ids: str = Field(..., alias="ADMIN_IDS")
    channel_id: int = Field(..., alias="CHANNEL_ID")

    # Google Sheets (Optional)
    google_credentials_path: str | None = Field(default=None, alias="GOOGLE_CREDENTIALS_PATH")
    spreadsheet_id: str | None = Field(default=None, alias="SPREADSHEET_ID")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")

    # Application config (loaded from config.json)
    app_config: AppConfig | None = None

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> str:
        """Parse admin IDs from comma-separated string."""
        if isinstance(v, str):
            return v
        return str(v)

    def get_admin_ids(self) -> list[int]:
        """Get list of admin user IDs."""
        return [int(id.strip()) for id in self.admin_ids.split(",") if id.strip()]

    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in self.get_admin_ids()

    def load_app_config(self, config_path: Path | None = None) -> None:
        """Load application configuration from config.json."""
        if config_path is None:
            # Default path
            config_path = Path(__file__).parent / "config.json"
        self.app_config = AppConfig.load_from_file(config_path)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        # Load app config from default location
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            _settings.load_app_config(config_path)
    return _settings


def init_settings(env_file: str | None = None) -> Settings:
    """Initialize settings with optional custom env file."""
    global _settings
    if env_file:
        _settings = Settings(_env_file=env_file)
    else:
        _settings = Settings()

    # Load app config
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        _settings.load_app_config(config_path)

    return _settings
