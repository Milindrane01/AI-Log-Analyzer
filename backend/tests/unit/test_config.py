"""Settings tests: env loading, validation, caching."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_defaults_are_safe_for_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_ENVIRONMENT", raising=False)
    s = Settings(_env_file=None)  # ignore any local .env — test pure defaults

    assert s.environment == "development"
    assert s.debug is False  # debug must be opt-in, never default-on
    assert s.is_production is False


def test_env_vars_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("APP_JWT_SECRET_KEY", "a-real-production-secret")
    monkeypatch.setenv("APP_LOG_LEVEL", "WARNING")

    s = Settings(_env_file=None)

    assert s.environment == "production"
    assert s.is_production is True
    assert s.log_level == "WARNING"


def test_invalid_environment_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "staging-ish")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()  # same object — read env once
