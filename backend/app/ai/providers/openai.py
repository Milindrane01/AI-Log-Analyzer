"""OpenAI provider via raw HTTP (httpx) with strict structured output.

Deliberately NOT the openai SDK: one endpoint, one schema — httpx keeps the
dependency tree flat and makes the request fully visible (useful when teaching
and when debugging token spend).
"""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
import structlog

from app.ai.prompts.analysis import SYSTEM_PROMPT, build_user_prompt
from app.ai.providers.base import (
    InsightRequest,
    InsightResult,
    LLMError,
    ProviderResponse,
    ProviderUsage,
)
from app.core.config import Settings

log = structlog.get_logger()


class OpenAIProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def analyze_group(self, request: InsightRequest) -> ProviderResponse:
        payload = {
            "model": self._settings.openai_model_cheap,
            "temperature": 0.2,  # diagnosis wants consistency, not creativity
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(request)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "error_insight",
                    "strict": True,
                    "schema": _strict_schema(),
                },
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._settings.ai_timeout_seconds) as client:
                resp = await client.post(
                    f"{self._settings.openai_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._settings.openai_api_key}"},
                    json=payload,
                )
            resp.raise_for_status()
            body = resp.json()
            content = body["choices"][0]["message"]["content"]
            result = InsightResult.model_validate(json.loads(content))
            usage = body.get("usage", {})
            return ProviderResponse(
                result=result,
                usage=ProviderUsage(
                    model=body.get("model", self._settings.openai_model_cheap),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                ),
            )
        except httpx.HTTPError as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc
        except (KeyError, json.JSONDecodeError, ValueError) as exc:
            raise LLMError(f"Unparseable OpenAI response: {exc}") from exc

    async def stream_chat(self, system: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yield answer tokens from a streaming chat completion (SSE passthrough)."""
        payload = {
            "model": self._settings.openai_model_cheap,
            "temperature": 0.2,
            "stream": True,
            "messages": [{"role": "system", "content": system}, *messages],
        }
        try:
            async with (
                httpx.AsyncClient(timeout=self._settings.ai_timeout_seconds) as client,
                client.stream(
                    "POST",
                    f"{self._settings.openai_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._settings.openai_api_key}"},
                    json=payload,
                ) as resp,
            ):
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    try:
                        delta = json.loads(line[6:])["choices"][0]["delta"]
                    except (KeyError, json.JSONDecodeError, IndexError):
                        continue
                    if content := delta.get("content"):
                        yield content
        except httpx.HTTPError as exc:
            raise LLMError(f"OpenAI stream failed: {exc}") from exc


def _strict_schema() -> dict[str, Any]:
    """InsightResult as OpenAI strict-mode JSON schema (no defaults, all required)."""
    schema = InsightResult.model_json_schema()
    schema["additionalProperties"] = False
    schema["required"] = list(schema["properties"].keys())
    return schema
