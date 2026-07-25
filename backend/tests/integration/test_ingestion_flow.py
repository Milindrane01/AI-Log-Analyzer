"""End-to-end ingestion: paste/upload → pipeline (inline) → poll → groups."""

import io

from httpx import AsyncClient

SAMPLE_LOG = """\
2026-07-15 10:12:14 ERROR Database connection timeout for user 8231
2026-07-15 10:12:15 ERROR Database connection timeout for user 9440
2026-07-15 10:12:16 INFO Health check passed
2026-07-15 10:12:17 WARNING Slow query took 2140 ms
2026-07-15 10:12:18 ERROR Database connection timeout for user 1102
2026-07-15 10:12:19 CRITICAL Out of memory, killing worker 4
"""


async def _paste(client: AsyncClient, headers: dict, content: str = SAMPLE_LOG) -> dict:
    resp = await client.post("/api/v1/logs/paste", json={"content": content}, headers=headers)
    assert resp.status_code == 202, resp.text
    return resp.json()


async def test_paste_to_completed_analysis(client: AsyncClient, auth_headers: dict) -> None:
    accepted = await _paste(client, auth_headers)
    assert accepted["status"] == "pending"  # snapshot at accept time

    # InlineTaskQueue ran the pipeline during the request; poll shows the result.
    resp = await client.get(f"/api/v1/analyses/{accepted['analysis_id']}", headers=auth_headers)
    assert resp.status_code == 200
    analysis = resp.json()

    assert analysis["status"] == "completed"
    assert analysis["total_lines"] == 6
    assert analysis["error_lines"] == 5  # 3 timeouts + 1 warning + 1 critical
    assert analysis["group_count"] == 3  # timeouts grouped; warning; critical


async def test_groups_are_deduplicated_and_ordered(client: AsyncClient, auth_headers: dict) -> None:
    accepted = await _paste(client, auth_headers)

    resp = await client.get(
        f"/api/v1/analyses/{accepted['analysis_id']}/groups", headers=auth_headers
    )
    assert resp.status_code == 200
    page = resp.json()

    assert page["total"] == 3
    top = page["items"][0]  # ordered by count desc
    assert top["count"] == 3
    assert "<n>" in top["template"]  # user ids normalized out
    assert top["severity"] == "high"
    assert len(top["sample_lines"]) == 3

    severities = {item["severity"] for item in page["items"]}
    assert severities == {"high", "medium", "critical"}


async def test_upload_multipart_file(client: AsyncClient, auth_headers: dict) -> None:
    file = io.BytesIO(SAMPLE_LOG.encode())
    resp = await client.post(
        "/api/v1/logs",
        files={"file": ("app.log", file, "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 202

    analysis = (
        await client.get(f"/api/v1/analyses/{resp.json()['analysis_id']}", headers=auth_headers)
    ).json()
    assert analysis["status"] == "completed"
    assert analysis["group_count"] == 3


async def test_json_format_detected(client: AsyncClient, auth_headers: dict) -> None:
    json_log = "\n".join(
        f'{{"timestamp": "2026-07-15T10:12:1{i}Z", "level": "error", "message": "boom {i}"}}'
        for i in range(4)
    )
    accepted = await _paste(client, auth_headers, json_log)
    analysis = (
        await client.get(f"/api/v1/analyses/{accepted['analysis_id']}", headers=auth_headers)
    ).json()

    assert analysis["status"] == "completed"
    assert analysis["group_count"] == 1  # "boom <n>" — all four are one problem


async def test_ingestion_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/logs/paste", json={"content": "x"})
    assert resp.status_code == 401


async def test_oversized_paste_rejected(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/api/v1/logs/paste",
        json={"content": "x" * (1024 * 1024 + 10)},
        headers=auth_headers,
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "file_too_large"


async def test_other_users_analysis_is_404(client: AsyncClient, auth_headers: dict) -> None:
    accepted = await _paste(client, auth_headers)

    other = {"email": "intruder@example.com", "password": "another-long-pass"}
    await client.post("/api/v1/auth/register", json=other)
    other_tokens = (await client.post("/api/v1/auth/login", json=other)).json()

    resp = await client.get(
        f"/api/v1/analyses/{accepted['analysis_id']}",
        headers={"Authorization": f"Bearer {other_tokens['access_token']}"},
    )
    assert resp.status_code == 404  # not 403: existence is not leaked


async def test_empty_paste_rejected(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/api/v1/logs/paste", json={"content": "   \n  "}, headers=auth_headers
    )
    assert resp.status_code == 400
