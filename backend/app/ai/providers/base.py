"""Provider contract + typed request/response.

The pipeline speaks THESE types only. Swapping OpenAI→Anthropic→local model, or
mocking in tests, never touches pipeline code.
"""

from collections.abc import AsyncIterator
from typing import Literal, Protocol

from pydantic import BaseModel, Field


class LLMError(Exception):
    """Any provider failure: network, timeout, quota, unparseable output."""


class InsightRequest(BaseModel):
    """Everything the model needs about one error group. No user PII fields."""

    level: str
    template: str
    count: int
    sample_lines: list[str]
    detected_format: str | None = None


class InsightResult(BaseModel):
    """Schema-validated model output. This IS the response_format sent to OpenAI."""

    error_type: str = Field(
        max_length=64, description="Short category, e.g. 'Database Connectivity'"
    )
    severity: Literal["critical", "high", "medium", "low"]
    root_cause: str = Field(max_length=1000)
    possible_reasons: list[str] = Field(max_length=6)
    explanation: str = Field(max_length=2000, description="Beginner-friendly plain language")
    suggested_fix: str = Field(max_length=1000)
    recommended_commands: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)


class ProviderUsage(BaseModel):
    model: str = "unknown"
    prompt_tokens: int = 0
    completion_tokens: int = 0


class ProviderResponse(BaseModel):
    result: InsightResult
    usage: ProviderUsage


class LLMProvider(Protocol):
    async def analyze_group(self, request: InsightRequest) -> ProviderResponse:
        """Analyze one error group. Raises LLMError on any failure."""
        ...


class ChatProvider(Protocol):
    def stream_chat(self, system: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yield answer tokens for a streaming chat completion."""
        ...
