"""Application entry point — the app factory.

Why a factory instead of a module-level `app = FastAPI()` with side effects:
1. Tests can build a fresh app with different settings per test.
2. Import order stops mattering (no hidden import-time side effects).
3. Configuration happens in exactly one visible place.

Run (dev):    uvicorn app.main:app --reload
Run (prod):   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.db import dispose_engine, init_engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.metrics import setup_metrics
from app.core.queue import CeleryTaskQueue

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook.

    Everything before `yield` runs once at startup, everything after at
    shutdown. Long-lived resources (DB pool, redis clients, ML models) are
    created here — once — and shared across requests.
    """
    settings = get_settings()
    init_engine(app, settings)  # connection pool: created once, shared by all requests
    app.state.task_queue = CeleryTaskQueue()  # tests override with InlineTaskQueue
    # Embedder is always available (chat RAG needs it even without qdrant).
    if settings.embedding_backend == "sentence-transformers":
        from app.ai.embeddings.sentence_transformer import SentenceTransformerEmbedder

        app.state.embedder = SentenceTransformerEmbedder(settings.embedding_model)
    else:
        from app.ai.embeddings.hashing import HashingEmbedder

        app.state.embedder = HashingEmbedder()
    app.state.vector_store = None
    if settings.qdrant_url:
        from app.ai.vectorstore.qdrant import QdrantVectorStore

        app.state.vector_store = QdrantVectorStore(settings.qdrant_url, dim=app.state.embedder.dim)
    # LLM provider for in-request AI (chat). None = chat returns 503.
    app.state.llm_provider = None
    if settings.ai_enabled:
        from app.ai.providers.openai import OpenAIProvider

        app.state.llm_provider = OpenAIProvider(settings)
    log.info(
        "application_startup",
        app=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )
    yield
    await dispose_engine(app)
    log.info("application_shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(log_level=settings.log_level, json_logs=settings.log_json)

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
        # Hide interactive docs in production: shrinks attack surface.
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )
    register_exception_handlers(app)
    setup_metrics(app)  # /metrics + RED middleware
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
