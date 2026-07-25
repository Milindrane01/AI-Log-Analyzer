"""Hybrid retrieval over chunks: lexical-first scoring + embedding cosine.

Why lexical-first for LOGS specifically: a 40-line chunk is dominated by
repeated noise lines (heartbeats), so bag-of-words cosine drowns the one rare
error term the user is asking about. Query-term coverage (with prefix matching
as crude stemming: "time" matches "timeout") is the primary signal; cosine is
the semantic tiebreaker — and does the heavy lifting once the production
sentence-transformer embedder is active.

The index is EPHEMERAL — built per chat request from the file on disk. At our
chunk cap (2000) with the hashing embedder that's milliseconds; with sentence
transformers it's the latency budget of one message. A persisted chunk index
in Qdrant is the documented optimization when usage justifies it (module doc).
"""

import re
from dataclasses import dataclass

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.rag.chunking import Chunk

_TOKEN = re.compile(r"[a-z0-9]{2,}")
COSINE_WEIGHT = 0.5  # secondary signal (dominant again with semantic embedders)
MIN_SCORE = 0.2  # ≈ one query term matched; below this → refuse, don't guess
_STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "was",
    "did",
    "do",
    "what",
    "why",
    "how",
    "when",
    "who",
    "with",
    "in",
    "on",
    "at",
    "of",
    "to",
    "and",
    "or",
}


@dataclass(slots=True)
class ScoredChunk:
    chunk: Chunk
    score: float


async def retrieve(
    embedder: EmbeddingProvider, chunks: list[Chunk], query: str, top_k: int = 6
) -> list[ScoredChunk]:
    if not chunks:
        return []
    vectors = await embedder.embed([c.text for c in chunks])
    [query_vec] = await embedder.embed([query])
    query_tokens = [t for t in set(_TOKEN.findall(query.lower())) if t not in _STOPWORDS]

    scored: list[ScoredChunk] = []
    for chunk, vec in zip(chunks, vectors, strict=True):
        cosine = sum(a * b for a, b in zip(query_vec, vec, strict=True))
        overlap = 0.0
        if query_tokens:
            chunk_tokens = set(_TOKEN.findall(chunk.text.lower()))
            hits = sum(
                1
                for token in query_tokens
                # exact, or prefix either direction ("time"~"timeout")
                if token in chunk_tokens
                or any(c.startswith(token) or token.startswith(c) for c in chunk_tokens)
            )
            overlap = hits / len(query_tokens)
        scored.append(ScoredChunk(chunk=chunk, score=overlap + COSINE_WEIGHT * cosine))

    scored.sort(key=lambda s: s.score, reverse=True)
    return [s for s in scored[:top_k] if s.score >= MIN_SCORE]
