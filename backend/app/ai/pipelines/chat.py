"""Grounded chat pipeline.

Hallucination defense IN CODE, not just prompt: if retrieval scores are too
weak, we refuse deterministically and never call the LLM at all. The prompt
rule is the second line of defense, not the first.
"""

from collections.abc import AsyncIterator

import structlog

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.prompts.chat import SYSTEM_PROMPT, build_context_block
from app.ai.rag.chunking import chunk_lines
from app.ai.rag.retriever import ScoredChunk, retrieve

log = structlog.get_logger()

REFUSAL = "I don't see anything about that in this log."
HISTORY_TURNS = 6  # last N messages sent as conversational context


class ChatResult:
    def __init__(self) -> None:
        self.citations: list[dict[str, int]] = []
        self.answer_parts: list[str] = []

    @property
    def answer(self) -> str:
        return "".join(self.answer_parts)


async def stream_chat_answer(
    provider,  # object with stream_chat(system, messages) -> AsyncIterator[str]
    embedder: EmbeddingProvider,
    file_path: str,
    history: list[dict[str, str]],  # [{"role","content"}] prior turns
    question: str,
    result: ChatResult,
) -> AsyncIterator[str]:
    """Yield answer tokens; populate `result` with citations + full text."""
    with open(file_path, encoding="utf-8", errors="replace") as fh:
        chunks = chunk_lines(fh.readlines())
    retrieved = await retrieve(embedder, chunks, question)

    if not retrieved:
        # Deterministic refusal — zero LLM calls for unanswerable questions.
        result.answer_parts.append(REFUSAL)
        yield REFUSAL
        return

    result.citations = [
        {"start_line": s.chunk.start_line, "end_line": s.chunk.end_line} for s in retrieved
    ]
    messages = [
        *history[-HISTORY_TURNS:],
        {"role": "user", "content": build_context_block(retrieved, question)},
    ]
    async for token in provider.stream_chat(SYSTEM_PROMPT, messages):
        result.answer_parts.append(token)
        yield token
    log.info("chat_answered", chunks_used=len(retrieved), answer_chars=len(result.answer))


def top_chunks_for_test(retrieved: list[ScoredChunk]) -> list[str]:  # pragma: no cover
    return [s.chunk.text for s in retrieved]
