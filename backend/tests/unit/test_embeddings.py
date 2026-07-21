"""Hashing embedder + in-memory store: the similarity math tests rely on."""

import math

from app.ai.embeddings.hashing import HashingEmbedder
from app.ai.vectorstore.base import VectorPoint
from app.ai.vectorstore.memory import InMemoryVectorStore


async def test_vectors_are_normalized_and_deterministic() -> None:
    embedder = HashingEmbedder()
    [v1] = await embedder.embed(["database connection timeout"])
    [v2] = await embedder.embed(["database connection timeout"])

    assert v1 == v2
    assert math.isclose(sum(x * x for x in v1), 1.0, rel_tol=1e-9)


async def test_related_texts_score_higher_than_unrelated() -> None:
    embedder = HashingEmbedder()
    [base, related, unrelated] = await embedder.embed(
        [
            "connection timeout to postgres database",
            "postgres database connection refused",
            "disk quota exceeded on volume",
        ]
    )
    related_score = sum(a * b for a, b in zip(base, related, strict=True))
    unrelated_score = sum(a * b for a, b in zip(base, unrelated, strict=True))

    assert related_score > unrelated_score
    assert related_score > 0.4  # above the service threshold


async def test_store_filters_by_user() -> None:
    embedder = HashingEmbedder()
    store = InMemoryVectorStore()
    [vec] = await embedder.embed(["database timeout"])
    await store.upsert(
        [
            VectorPoint(id="mine", vector=vec, payload={"user_id": "u1"}),
            VectorPoint(id="theirs", vector=vec, payload={"user_id": "u2"}),
        ]
    )

    hits = await store.search(vec, user_id="u1", limit=10)

    assert [h.id for h in hits] == ["mine"]  # perfect match for u2 is invisible


async def test_store_orders_by_similarity() -> None:
    embedder = HashingEmbedder()
    store = InMemoryVectorStore()
    vectors = await embedder.embed(
        ["postgres connection timeout", "postgres timeout again", "cache miss ratio high"]
    )
    await store.upsert(
        [
            VectorPoint(id=f"p{i}", vector=v, payload={"user_id": "u1"})
            for i, v in enumerate(vectors)
        ]
    )

    [query] = await embedder.embed(["connection timeout postgres"])
    hits = await store.search(query, user_id="u1", limit=3)

    assert hits[0].id == "p0"  # most similar first
    assert hits[-1].id == "p2"  # unrelated last
