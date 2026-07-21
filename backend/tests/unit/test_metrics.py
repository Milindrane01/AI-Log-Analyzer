"""Metrics endpoint + RED middleware."""

from httpx import AsyncClient

from app.core import metrics


async def test_metrics_endpoint_exposes_prometheus_text(client: AsyncClient) -> None:
    metrics.reset()
    await client.get("/api/v1/health")

    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds_count" in body


async def test_paths_are_templated_not_raw(client: AsyncClient, auth_headers: dict) -> None:
    metrics.reset()
    # Two different analysis ids must collapse to ONE series (high-cardinality guard).
    await client.get("/api/v1/analyses/abc-111", headers=auth_headers)
    await client.get("/api/v1/analyses/def-222", headers=auth_headers)

    body = (await client.get("/metrics")).text
    assert "/analyses/{analysis_id}" in body  # route template, ids collapsed to one series
    assert "abc-111" not in body and "def-222" not in body


async def test_metrics_path_not_self_measured(client: AsyncClient) -> None:
    metrics.reset()
    await client.get("/metrics")
    body = (await client.get("/metrics")).text
    assert 'path="/metrics"' not in body
