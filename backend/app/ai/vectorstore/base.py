"""Vector store contract.

The user_id filter is MANDATORY on search — payload filtering is the tenant
isolation mechanism (ADR-003). A store without filtering cannot implement this
interface correctly, which is exactly the point.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VectorHit:
    id: str
    score: float  # cosine similarity, higher = closer
    payload: dict[str, Any]


class VectorStore(Protocol):
    async def healthy(self) -> bool: ...

    async def upsert(self, points: list[VectorPoint]) -> None: ...

    async def search(
        self, vector: list[float], user_id: str, limit: int = 10
    ) -> list[VectorHit]: ...
