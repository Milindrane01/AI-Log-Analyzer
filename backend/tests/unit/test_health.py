"""Health endpoint tests: contract + status codes."""

from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "AI Log Analyzer"
    assert body["version"]  # non-empty; exact value is config's business


async def test_readiness_returns_ready(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health/ready")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["app"] is True
    assert body["checks"]["database"] is True
    assert body["checks"]["vector_store"] is True  # in-memory store wired in tests


async def test_unknown_route_is_404(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/nope")
    assert resp.status_code == 404
