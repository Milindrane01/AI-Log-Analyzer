"""Chat-with-logs flow: SSE stream, grounding, persistence, isolation."""

import json

from httpx import AsyncClient

from app.ai.providers.mock import MockLLMProvider

CHAT_LOG = """\
2026-07-15 10:12:14 ERROR Database connection timeout for user 8231
2026-07-15 10:12:15 INFO Retrying connection to postgres
2026-07-15 10:12:16 ERROR Database connection timeout for user 8231
"""


async def _prepare(client: AsyncClient, headers: dict) -> str:
    """Upload a log; return its log_file_id. Enables mock chat provider."""
    app = client._transport.app  # type: ignore[attr-defined]
    app.state.llm_provider = MockLLMProvider()
    resp = await client.post("/api/v1/logs/paste", json={"content": CHAT_LOG}, headers=headers)
    return resp.json()["log_file_id"]


def _parse_sse(raw: str) -> list[dict]:
    return [json.loads(line[6:]) for line in raw.splitlines() if line.startswith("data: ")]


async def test_chat_streams_grounded_answer(client: AsyncClient, auth_headers: dict) -> None:
    file_id = await _prepare(client, auth_headers)

    resp = await client.post(
        f"/api/v1/logs/{file_id}/chat",
        json={"message": "what happened with the database?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    tokens = [e["text"] for e in events if e["type"] == "token"]
    done = next(e for e in events if e["type"] == "done")

    answer = "".join(tokens)
    assert "[lines 1-" in answer  # cites line ranges
    assert "Database connection timeout" in answer  # quotes the evidence
    assert done["citations"], "citations recorded on the message"


async def test_chat_persists_conversation(client: AsyncClient, auth_headers: dict) -> None:
    file_id = await _prepare(client, auth_headers)
    await client.post(
        f"/api/v1/logs/{file_id}/chat",
        json={"message": "what happened to the database connection?"},
        headers=auth_headers,
    )

    history = (
        await client.get(f"/api/v1/logs/{file_id}/chat", headers=auth_headers)
    ).json()

    roles = [m["role"] for m in history["items"]]
    assert roles == ["user", "assistant"]
    assert history["items"][1]["citations"]


async def test_unanswerable_question_gets_refusal_not_guess(
    client: AsyncClient, auth_headers: dict
) -> None:
    file_id = await _prepare(client, auth_headers)
    app = client._transport.app  # type: ignore[attr-defined]
    provider: MockLLMProvider = app.state.llm_provider
    calls_before = provider.calls

    resp = await client.post(
        f"/api/v1/logs/{file_id}/chat",
        json={"message": "what is the kubernetes ingress certificate expiry?"},
        headers=auth_headers,
    )
    events = _parse_sse(resp.text)
    answer = "".join(e["text"] for e in events if e["type"] == "token")

    assert "don't see anything about that" in answer
    assert provider.calls == calls_before  # refusal happened in CODE, zero LLM calls


async def test_chat_503_when_ai_disabled(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post("/api/v1/logs/paste", json={"content": CHAT_LOG}, headers=auth_headers)
    file_id = resp.json()["log_file_id"]
    # conftest default: llm_provider is None

    resp = await client.post(
        f"/api/v1/logs/{file_id}/chat", json={"message": "hi?"}, headers=auth_headers
    )
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "ai_unavailable"


async def test_chat_isolated_between_users(client: AsyncClient, auth_headers: dict) -> None:
    file_id = await _prepare(client, auth_headers)

    other = {"email": "snoop@example.com", "password": "another-long-pass"}
    await client.post("/api/v1/auth/register", json=other)
    tokens = (await client.post("/api/v1/auth/login", json=other)).json()

    resp = await client.get(
        f"/api/v1/logs/{file_id}/chat",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == 404
