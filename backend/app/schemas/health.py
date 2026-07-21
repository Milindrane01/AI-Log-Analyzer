"""Health check response contracts."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness payload: 'the process is up and can serve requests'."""

    status: Literal["ok"]
    app: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness payload: 'the app AND its dependencies can do real work'.

    Dependency checks (postgres, redis, qdrant) are added in M2/M3 —
    the `checks` dict is the extension point.
    """

    status: Literal["ready", "degraded"]
    checks: dict[str, bool]
