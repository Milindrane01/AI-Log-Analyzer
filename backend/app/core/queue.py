"""Task queue abstraction.

The API depends on this interface, not on Celery: production enqueues to
Celery/Redis; tests use InlineQueue (runs the pipeline immediately, same event
loop, zero infrastructure). Same seam a real system uses to swap SQS/Celery/etc.
"""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.providers.base import LLMProvider
from app.ai.vectorstore.base import VectorStore


class TaskQueue(Protocol):
    async def enqueue_analysis(self, analysis_id: str) -> None: ...


class CeleryTaskQueue:
    """Production: hand the id to the Celery broker and return immediately."""

    async def enqueue_analysis(self, analysis_id: str) -> None:
        from app.workers.tasks import run_analysis_task  # deferred: worker deps

        run_analysis_task.delay(analysis_id)


class InlineTaskQueue:
    """Tests/dev-without-redis: run the pipeline right now, in-process."""

    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        provider: LLMProvider | None = None,
        embedder: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._provider = provider
        self._embedder = embedder
        self._vector_store = vector_store

    async def enqueue_analysis(self, analysis_id: str) -> None:
        from app.services.pipeline import run_analysis

        await run_analysis(
            analysis_id,
            self._sessionmaker,
            provider=self._provider,
            embedder=self._embedder,
            vector_store=self._vector_store,
        )
