"""Incident report + commands endpoints, with mock AI insights present."""

from httpx import AsyncClient

from app.ai.providers.mock import MockLLMProvider
from app.core.queue import InlineTaskQueue

LOG = """\
2026-07-15 10:12:14 ERROR Database connection timeout for user 8231
2026-07-15 10:12:15 ERROR Database connection timeout for user 9440
2026-07-15 10:12:18 CRITICAL Out of memory, killing worker 4
"""


async def _analyze_with_ai(client: AsyncClient, headers: dict) -> str:
    app = client._transport.app  # type: ignore[attr-defined]
    app.state.task_queue = InlineTaskQueue(
        app.state.db_sessionmaker, provider=MockLLMProvider()
    )
    resp = await client.post("/api/v1/logs/paste", json={"content": LOG}, headers=headers)
    return resp.json()["analysis_id"]


async def test_generate_and_fetch_report(client: AsyncClient, auth_headers: dict) -> None:
    analysis_id = await _analyze_with_ai(client, auth_headers)

    gen = await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)
    assert gen.status_code == 200, gen.text
    report = gen.json()

    assert "Incident report" in report["title"]
    md = report["markdown"]
    assert "## Summary" in md and "## Findings" in md and "## Prevention" in md
    assert "Database Connectivity" in md
    assert "kubectl get pods" in md  # rendered safe command in the report
    assert "rm -rf" not in md

    # Idempotent: regenerating updates in place, doesn't duplicate.
    again = await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)
    assert again.json()["id"] == report["id"]


async def test_download_markdown(client: AsyncClient, auth_headers: dict) -> None:
    analysis_id = await _analyze_with_ai(client, auth_headers)
    await client.post(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)

    resp = await client.get(f"/api/v1/analyses/{analysis_id}/report.md", headers=auth_headers)
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]
    assert resp.text.startswith("# Incident report")


async def test_commands_endpoint_for_group(client: AsyncClient, auth_headers: dict) -> None:
    analysis_id = await _analyze_with_ai(client, auth_headers)
    groups = (
        await client.get(f"/api/v1/analyses/{analysis_id}/groups", headers=auth_headers)
    ).json()["items"]
    db_group = next(g for g in groups if g["insight"]["payload"]["error_type"] == "Database Connectivity")

    resp = await client.get(
        f"/api/v1/analyses/{analysis_id}/groups/{db_group['id']}/commands", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["error_type"] == "Database Connectivity"
    assert any("kubectl" in c["command"] for c in body["commands"])


async def test_report_requires_completed_analysis_ownership(
    client: AsyncClient, auth_headers: dict
) -> None:
    analysis_id = await _analyze_with_ai(client, auth_headers)

    other = {"email": "nope@example.com", "password": "another-long-pass"}
    await client.post("/api/v1/auth/register", json=other)
    tokens = (await client.post("/api/v1/auth/login", json=other)).json()

    resp = await client.post(
        f"/api/v1/analyses/{analysis_id}/report",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 404  # not yours → doesn't exist


async def test_get_report_before_generation_is_404(
    client: AsyncClient, auth_headers: dict
) -> None:
    analysis_id = await _analyze_with_ai(client, auth_headers)
    resp = await client.get(f"/api/v1/analyses/{analysis_id}/report", headers=auth_headers)
    assert resp.status_code == 404
