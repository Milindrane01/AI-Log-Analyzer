"""Qdrant store via REST (httpx) — same flat-dependency choice as the OpenAI provider."""

import httpx
import structlog

from app.ai.vectorstore.base import VectorHit, VectorPoint

log = structlog.get_logger()

COLLECTION = "error_groups"


class QdrantVectorStore:
    def __init__(self, base_url: str, dim: int, timeout: float = 10.0) -> None:
        self._url = base_url.rstrip("/")
        self._dim = dim
        self._timeout = timeout
        self._ready = False

    async def _ensure_collection(self, client: httpx.AsyncClient) -> None:
        if self._ready:
            return
        resp = await client.put(
            f"{self._url}/collections/{COLLECTION}",
            json={"vectors": {"size": self._dim, "distance": "Cosine"}},
        )
        # 200 created, 409 already exists — both fine.
        if resp.status_code not in (200, 409):
            resp.raise_for_status()
        self._ready = True

    async def healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self._url}/collections")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def upsert(self, points: list[VectorPoint]) -> None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            await self._ensure_collection(client)
            resp = await client.put(
                f"{self._url}/collections/{COLLECTION}/points",
                json={
                    "points": [
                        {"id": p.id, "vector": p.vector, "payload": p.payload} for p in points
                    ]
                },
            )
            resp.raise_for_status()

    async def search(self, vector: list[float], user_id: str, limit: int = 10) -> list[VectorHit]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            await self._ensure_collection(client)
            resp = await client.post(
                f"{self._url}/collections/{COLLECTION}/points/search",
                json={
                    "vector": vector,
                    "limit": limit,
                    "with_payload": True,
                    # Server-side isolation filter — never post-filter client-side.
                    "filter": {"must": [{"key": "user_id", "match": {"value": user_id}}]},
                },
            )
            resp.raise_for_status()
            return [
                VectorHit(id=str(r["id"]), score=float(r["score"]), payload=r.get("payload") or {})
                for r in resp.json().get("result", [])
            ]
