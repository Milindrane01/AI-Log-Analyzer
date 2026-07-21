"""'Have we seen this before?' — cross-analysis similarity flow."""

from httpx import AsyncClient

INCIDENT_MONDAY = """\
2026-07-13 03:11:02 ERROR Connection timeout to postgres primary
2026-07-13 03:11:04 ERROR Connection timeout to postgres primary
"""
INCIDENT_TODAY = """\
2026-07-15 10:12:14 ERROR Postgres connection timeout while serving request 8812
"""
UNRELATED = """\
2026-07-14 09:00:00 ERROR TLS certificate for api.example.com expired
"""


async def _analyze(client: AsyncClient, headers: dict, content: str) -> str:
    resp = await client.post("/api/v1/logs/paste", json={"content": content}, headers=headers)
    return resp.json()["analysis_id"]


async def test_similar_incident_found_across_analyses(
    client: AsyncClient, auth_headers: dict
) -> None:
    monday_id = await _analyze(client, auth_headers, INCIDENT_MONDAY)
    await _analyze(client, auth_headers, UNRELATED)
    today_id = await _analyze(client, auth_headers, INCIDENT_TODAY)

    resp = await client.get(f"/api/v1/analyses/{today_id}/similar", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["enabled"] is True
    assert body["items"], "expected at least one similar incident"
    top = body["items"][0]
    assert top["analysis_id"] == monday_id  # found Monday's incident, not the TLS one
    assert "postgres" in top["template"]
    assert top["score"] > 0.4


async def test_own_analysis_excluded_from_similar(
    client: AsyncClient, auth_headers: dict
) -> None:
    analysis_id = await _analyze(client, auth_headers, INCIDENT_MONDAY)

    body = (
        await client.get(f"/api/v1/analyses/{analysis_id}/similar", headers=auth_headers)
    ).json()

    assert all(item["analysis_id"] != analysis_id for item in body["items"])


async def test_similarity_isolated_between_users(
    client: AsyncClient, auth_headers: dict
) -> None:
    await _analyze(client, auth_headers, INCIDENT_MONDAY)

    other = {"email": "other@example.com", "password": "another-long-pass"}
    await client.post("/api/v1/auth/register", json=other)
    tokens = (await client.post("/api/v1/auth/login", json=other)).json()
    other_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    other_analysis = await _analyze(client, other_headers, INCIDENT_TODAY)

    body = (
        await client.get(f"/api/v1/analyses/{other_analysis}/similar", headers=other_headers)
    ).json()

    assert body["items"] == []  # user A's incidents are invisible to user B


async def test_history_endpoint_lists_analyses(
    client: AsyncClient, auth_headers: dict
) -> None:
    await _analyze(client, auth_headers, INCIDENT_MONDAY)
    await _analyze(client, auth_headers, UNRELATED)

    resp = await client.get("/api/v1/analyses?limit=10", headers=auth_headers)
    assert resp.status_code == 200
    page = resp.json()

    assert page["total"] == 2
    assert len(page["items"]) == 2
    assert all(item["filename"] for item in page["items"])
    assert all(item["status"] == "completed" for item in page["items"])
