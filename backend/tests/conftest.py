"""Shared pytest fixtures.

Test database: SQLite (aiosqlite) — zero infrastructure. Task queue: InlineTaskQueue
runs the analysis pipeline immediately in-process, so ingestion tests exercise the
REAL pipeline without Celery/Redis. Uploads land in a per-test tmp dir.
"""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.ai.embeddings.hashing import HashingEmbedder
from app.ai.vectorstore.memory import InMemoryVectorStore
from app.core import ratelimit
from app.core.config import get_settings
from app.core.queue import InlineTaskQueue
from app.main import create_app
from app.models import Base


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Per-test isolation: fresh settings cache, fresh SQLite file, clean rate limits."""
    monkeypatch.setenv("APP_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("APP_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("APP_REDIS_URL", "")  # disables redis-dependent paths
    get_settings.cache_clear()
    ratelimit.reset()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """App with lifespan run, tables created, inline task queue."""
    app = create_app()
    async with LifespanManager(app):  # httpx alone does NOT run lifespan
        async with app.state.db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)  # tests: create_all; prod: alembic
        embedder = HashingEmbedder()
        store = InMemoryVectorStore()
        app.state.embedder = embedder
        app.state.vector_store = store
        app.state.task_queue = InlineTaskQueue(
            app.state.db_sessionmaker, embedder=embedder, vector_store=store
        )
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Registered + logged-in user; returns Authorization headers."""
    creds = {"email": "ops@example.com", "password": "a-long-passphrase"}
    await client.post("/api/v1/auth/register", json=creds)
    tokens = (await client.post("/api/v1/auth/login", json=creds)).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}
