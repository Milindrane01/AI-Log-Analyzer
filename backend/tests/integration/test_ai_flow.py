"""AI analysis flow with the mock provider wired through the real pipeline."""

from httpx import AsyncClient

from app.ai.providers.mock import MockLLMProvider
from app.core.queue import InlineTaskQueue

# The master prompt's example input.
BRIEF_EXAMPLE = """\
2026-07-15 10:12:14 ERROR Database connection timeout
Connection refused to PostgreSQL
"""

DB_TIMEOUT_LOG = """\
2026-07-15 10:12:14 ERROR Database connection timeout for user 8231
2026-07-15 10:12:15 ERROR Database connection timeout for user 9440
2026-07-15 10:12:18 CRITICAL Out of memory, killing worker 4
"""


def _use_mock(client: AsyncClient) -> MockLLMProvider:
    """Swap the inline queue for one that carries the mock AI provider."""
    app = client._transport.app  # type: ignore[attr-defined]
    provider = MockLLMProvider()
    app.state.task_queue = InlineTaskQueue(app.state.db_sessionmaker, provider=provider)
    return provider


async def _analyze(client: AsyncClient, headers: dict, content: str) -> dict:
    accepted = (
        await client.post("/api/v1/logs/paste", json={"content": content}, headers=headers)
    ).json()
    return (
        await client.get(f"/api/v1/analyses/{accepted['analysis_id']}/groups", headers=headers)
    ).json()


async def test_brief_example_produces_expected_shape(
    client: AsyncClient, auth_headers: dict
) -> None:
    _use_mock(client)
    page = await _analyze(client, auth_headers, BRIEF_EXAMPLE)

    top = page["items"][0]
    assert top["insight"] is not None
    payload = top["insight"]["payload"]

    # The contract from the project brief's "Expected Output".
    assert payload["error_type"] == "Database Connectivity"
    assert payload["severity"] in {"critical", "high"}
    assert "connection" in payload["root_cause"].lower()
    assert len(payload["possible_reasons"]) >= 3
    assert "kubectl get pods" in payload["recommended_commands"]
    assert 0.0 <= payload["confidence"] <= 1.0
    assert payload["explanation"]  # beginner-friendly text present


async def test_ai_refines_severity(client: AsyncClient, auth_headers: dict) -> None:
    _use_mock(client)
    page = await _analyze(client, auth_headers, DB_TIMEOUT_LOG)

    by_type = {i["insight"]["payload"]["error_type"]: i for i in page["items"]}
    # M3 heuristic said "high" (level=error); mock AI says DB connectivity is critical.
    assert by_type["Database Connectivity"]["severity"] == "critical"


async def test_fingerprint_cache_prevents_duplicate_llm_calls(
    client: AsyncClient, auth_headers: dict
) -> None:
    provider = _use_mock(client)

    await _analyze(client, auth_headers, DB_TIMEOUT_LOG)
    first_calls = provider.calls
    assert first_calls == 2  # two groups, two calls

    # Same errors again (new analysis): cache must serve both groups.
    page = await _analyze(client, auth_headers, DB_TIMEOUT_LOG)
    assert provider.calls == first_calls  # ZERO new LLM calls
    assert all(i["insight"]["from_cache"] for i in page["items"])


async def test_no_provider_means_groups_without_insights(
    client: AsyncClient, auth_headers: dict
) -> None:
    # Default conftest queue has provider=None (AI disabled) — graceful degradation.
    page = await _analyze(client, auth_headers, DB_TIMEOUT_LOG)

    assert page["total"] == 2  # analysis still completes fully
    assert all(item["insight"] is None for item in page["items"])


async def test_failing_provider_does_not_fail_analysis(
    client: AsyncClient, auth_headers: dict
) -> None:
    class ExplodingProvider:
        async def analyze_group(self, request):  # noqa: ANN001
            from app.ai.providers.base import LLMError

            raise LLMError("simulated outage")

    app = client._transport.app  # type: ignore[attr-defined]
    app.state.task_queue = InlineTaskQueue(app.state.db_sessionmaker, provider=ExplodingProvider())
    accepted = (
        await client.post(
            "/api/v1/logs/paste", json={"content": DB_TIMEOUT_LOG}, headers=auth_headers
        )
    ).json()
    analysis = (
        await client.get(f"/api/v1/analyses/{accepted['analysis_id']}", headers=auth_headers)
    ).json()

    assert analysis["status"] == "completed"  # degraded, not dead
    assert analysis["group_count"] == 2


async def test_injected_log_cannot_smuggle_commands(
    client: AsyncClient, auth_headers: dict
) -> None:
    """Even if a (mock) model echoed hostile commands, the filter drops them.

    Here we verify the guard at the pipeline boundary: craft a provider that
    returns a destructive command; storage must not contain it.
    """
    from app.ai.providers.base import InsightResult, ProviderResponse, ProviderUsage

    class NaiveProvider:
        async def analyze_group(self, request):  # noqa: ANN001
            return ProviderResponse(
                result=InsightResult(
                    error_type="X",
                    severity="high",
                    root_cause="r",
                    possible_reasons=["a"],
                    explanation="e",
                    suggested_fix="f",
                    recommended_commands=["kubectl get pods", "rm -rf /", "sudo reboot"],
                    confidence=0.9,
                ),
                usage=ProviderUsage(model="naive"),
            )

    app = client._transport.app  # type: ignore[attr-defined]
    app.state.task_queue = InlineTaskQueue(app.state.db_sessionmaker, provider=NaiveProvider())
    page = await _analyze(client, auth_headers, BRIEF_EXAMPLE)

    commands = page["items"][0]["insight"]["payload"]["recommended_commands"]
    assert commands == ["kubectl get pods"]  # destructive ones silently dropped
