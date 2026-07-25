"""Application configuration.

Single source of truth for all runtime settings, following 12-factor:
config lives in the environment, never in code. Every value has a safe
development default EXCEPT secrets, which must never default in production
(validator below refuses recognizable dev secrets).
"""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]

# Deliberately recognizable so production boot can refuse it outright.
_DEV_JWT_SECRET = "dev-secret-do-not-use-in-prod"  # noqa: S105 -- placeholder, not a real secret


class Settings(BaseSettings):
    """Typed, validated application settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- identity ---
    app_name: str = "AI Log Analyzer"
    version: str = "0.1.0"

    # --- runtime behaviour ---
    environment: Environment = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = True

    # --- API ---
    api_v1_prefix: str = "/api/v1"

    # --- database ---
    database_url: str = (
        "postgresql+asyncpg://loganalyzer:change-me-in-dev-too@localhost:5432/loganalyzer"
    )

    # --- redis / background jobs ---
    # Empty string disables redis-dependent features (tests run without redis).
    redis_url: str = "redis://localhost:6379/0"

    # --- AI (Milestone 4) ---
    # Empty key = AI disabled: analyses complete with groups but no insights.
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model_cheap: str = "gpt-4o-mini"  # classification-grade work
    openai_model_strong: str = "gpt-4o"  # root-cause-grade work (M4 uses cheap by default)
    ai_max_groups_per_analysis: int = 10  # cost cap: only top-N groups get AI
    ai_timeout_seconds: float = 30.0

    # --- similarity / vectors (Milestone 5) ---
    qdrant_url: str = ""  # e.g. http://qdrant:6333; empty = similarity disabled
    embedding_backend: str = "hashing"  # hashing | sentence-transformers
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- ingestion limits ---
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 50 * 1024 * 1024  # 50MB files
    max_paste_bytes: int = 1 * 1024 * 1024  # 1MB pasted text

    # --- auth / JWT ---
    jwt_secret_key: str = _DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _no_dev_secrets_in_production(self) -> "Settings":
        if self.is_production and self.jwt_secret_key == _DEV_JWT_SECRET:
            raise ValueError("APP_JWT_SECRET_KEY must be set to a real secret in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Process-wide Settings instance (lazy singleton).

    Tests bypass via Settings(...) directly or get_settings.cache_clear().
    """
    return Settings()
