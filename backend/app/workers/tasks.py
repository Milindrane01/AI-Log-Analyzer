"""Celery tasks. Celery is sync-land: each task run creates a private async
engine, runs the pipeline via asyncio.run, and disposes it. A pooled engine
can't be shared across Celery's forked workers — per-task engines are the
simple, correct default at this scale."""

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.workers.celery_app import celery_app


@celery_app.task(name="analysis.run", max_retries=2, autoretry_for=(ConnectionError,))
def run_analysis_task(analysis_id: str) -> None:
    from app.services.pipeline import run_analysis

    async def _run() -> None:
        settings = get_settings()
        provider = None
        if settings.ai_enabled:
            from app.ai.providers.openai import OpenAIProvider

            provider = OpenAIProvider(settings)
        embedder = vector_store = None
        if settings.qdrant_url:
            if settings.embedding_backend == "sentence-transformers":
                from app.ai.embeddings.sentence_transformer import SentenceTransformerEmbedder

                embedder = SentenceTransformerEmbedder(settings.embedding_model)
            else:
                from app.ai.embeddings.hashing import HashingEmbedder

                embedder = HashingEmbedder()
            from app.ai.vectorstore.qdrant import QdrantVectorStore

            vector_store = QdrantVectorStore(settings.qdrant_url, dim=embedder.dim)
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        try:
            await run_analysis(
                analysis_id,
                async_sessionmaker(engine, expire_on_commit=False),
                provider=provider,
                embedder=embedder,
                vector_store=vector_store,
            )
        finally:
            await engine.dispose()

    asyncio.run(_run())
