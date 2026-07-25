"""Similar-incident search: index error groups, find related past incidents."""

from typing import Any

import structlog

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.vectorstore.base import VectorPoint, VectorStore
from app.models import ErrorGroup

log = structlog.get_logger()

SIMILARITY_THRESHOLD = 0.4  # below this, "similar" would be noise


async def index_groups(
    embedder: EmbeddingProvider,
    store: VectorStore,
    groups: list[ErrorGroup],
    user_id: str,
    analysis_id: str,
) -> int:
    """Embed group templates and store them with an isolation payload."""
    if not groups:
        return 0
    vectors = await embedder.embed([g.template for g in groups])
    points = [
        VectorPoint(
            id=group.id,  # group uuid = point id (idempotent upsert)
            vector=vector,
            payload={
                "user_id": user_id,
                "analysis_id": analysis_id,
                "group_id": group.id,
                "template": group.template,
                "level": group.level,
                "severity": group.severity.value,
                "fingerprint": group.fingerprint,
            },
        )
        for group, vector in zip(groups, vectors, strict=True)
    ]
    await store.upsert(points)
    log.info("groups_indexed", analysis_id=analysis_id, count=len(points))
    return len(points)


async def find_similar(
    embedder: EmbeddingProvider,
    store: VectorStore,
    group: ErrorGroup,
    user_id: str,
    exclude_analysis_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Past incidents similar to this group, excluding the current analysis."""
    [vector] = await embedder.embed([group.template])
    hits = await store.search(vector, user_id=user_id, limit=limit + 20)
    results: list[dict[str, Any]] = []
    for hit in hits:
        if hit.payload.get("analysis_id") == exclude_analysis_id:
            continue  # same upload isn't a "past incident"
        if hit.score < SIMILARITY_THRESHOLD:
            continue
        results.append(
            {
                "group_id": hit.payload.get("group_id"),
                "analysis_id": hit.payload.get("analysis_id"),
                "template": hit.payload.get("template"),
                "severity": hit.payload.get("severity"),
                "score": round(hit.score, 3),
            }
        )
        if len(results) >= limit:
            break
    return results
