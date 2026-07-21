"""In-memory vector store: pure-python cosine search for tests/dev."""

from app.ai.vectorstore.base import VectorHit, VectorPoint


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._points: dict[str, VectorPoint] = {}

    async def healthy(self) -> bool:
        return True

    async def upsert(self, points: list[VectorPoint]) -> None:
        for point in points:
            self._points[point.id] = point

    async def search(
        self, vector: list[float], user_id: str, limit: int = 10
    ) -> list[VectorHit]:
        hits = [
            VectorHit(id=p.id, score=_dot(vector, p.vector), payload=p.payload)
            for p in self._points.values()
            if p.payload.get("user_id") == user_id  # isolation, always
        ]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))  # inputs are normalized
