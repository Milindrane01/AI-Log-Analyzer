"""Timeline + investigation end-to-end over a multi-service cascade log."""

from httpx import AsyncClient

# redis degrades first, then DB timeouts, then 502s — a classic cascade.
CASCADE_LOG = """\
2026-07-15 10:11:02 ERROR Redis connection pool exhausted
2026-07-15 10:11:05 ERROR Redis connection pool exhausted
2026-07-15 10:12:14 ERROR Database connection timeout for user 8231
2026-07-15 10:12:20 ERROR Database connection timeout for user 9440
2026-07-15 10:13:31 ERROR Upstream returned HTTP 502
2026-07-15 10:13:47 ERROR Upstream returned HTTP 502
"""


async def _analyze(client: AsyncClient, headers: dict) -> str:
    resp = await client.post("/api/v1/logs/paste", json={"content": CASCADE_LOG}, headers=headers)
    return resp.json()["analysis_id"]


async def test_timeline_orders_events_and_marks_first_failure(
    client: AsyncClient, auth_headers: dict
) -> None:
    analysis_id = await _analyze(client, auth_headers)

    resp = await client.get(f"/api/v1/analyses/{analysis_id}/timeline", headers=auth_headers)
    assert resp.status_code == 200
    events = resp.json()["events"]

    assert len(events) == 3
    assert events[0]["first_seen"] <= events[1]["first_seen"] <= events[2]["first_seen"]
    first = [e for e in events if e["is_first_failure"]]
    assert len(first) == 1
    assert "redis" in first[0]["label"].lower()  # redis degraded first


async def test_investigation_produces_verified_causal_conclusion(
    client: AsyncClient, auth_headers: dict
) -> None:
    analysis_id = await _analyze(client, auth_headers)

    resp = await client.post(f"/api/v1/analyses/{analysis_id}/investigate", headers=auth_headers)
    assert resp.status_code == 200
    inv = resp.json()

    assert inv["status"] == "completed"
    assert [s["agent"] for s in inv["steps"]] == ["planner", "investigator", "verifier"]
    assert "redis" in inv["conclusion"].lower()
    assert inv["verified"] is True
    assert inv["total_steps"] == 3


async def test_investigation_persists_and_is_retrievable(
    client: AsyncClient, auth_headers: dict
) -> None:
    analysis_id = await _analyze(client, auth_headers)
    await client.post(f"/api/v1/analyses/{analysis_id}/investigate", headers=auth_headers)

    resp = await client.get(f"/api/v1/analyses/{analysis_id}/investigation", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["steps"], "full trace retrievable"


async def test_investigation_isolated_by_user(client: AsyncClient, auth_headers: dict) -> None:
    analysis_id = await _analyze(client, auth_headers)

    other = {"email": "rival@example.com", "password": "another-long-pass"}
    await client.post("/api/v1/auth/register", json=other)
    tokens = (await client.post("/api/v1/auth/login", json=other)).json()

    resp = await client.post(
        f"/api/v1/analyses/{analysis_id}/investigate",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 404
