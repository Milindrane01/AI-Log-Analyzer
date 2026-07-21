"""Health endpoints.

Two distinct probes, matching Kubernetes semantics:

- /health       (liveness) : process is alive. K8s restarts the pod if this fails.
- /health/ready (readiness): dependencies are reachable. K8s stops routing
  traffic (but does NOT restart) if this fails.

Conflating them is a classic outage amplifier: if liveness checked the DB,
a DB blip would make K8s restart every healthy API pod at once.
"""

import structlog
from fastapi import APIRouter, Request
from sqlalchemy import text

from app.api.deps import SettingsDep
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])
log = structlog.get_logger()


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )


async def _store_ok(store) -> bool:
    try:
        return await store.healthy()
    except Exception:
        log.warning("vector_store_readiness_ping_failed", exc_info=True)
        return False


async def _db_ok(request: Request) -> bool:
    try:
        async with request.app.state.db_sessionmaker() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        log.warning("db_readiness_ping_failed", exc_info=True)
        return False


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def readiness(request: Request) -> ReadinessResponse:
    checks: dict[str, bool] = {"app": True, "database": await _db_ok(request)}
    store = getattr(request.app.state, "vector_store", None)
    if store is not None:  # only checked when similarity search is configured
        checks["vector_store"] = await _store_ok(store)
    ready = all(checks.values())
    if not ready:
        log.warning("readiness_check_failed", checks=checks)
    return ReadinessResponse(status="ready" if ready else "degraded", checks=checks)
