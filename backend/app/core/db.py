"""Async database wiring.

The engine (connection pool) is created ONCE in the app lifespan and stored on
app.state — never at import time. Each request gets its own short-lived session
via the get_db dependency: sessions are cheap, connections are pooled.
"""

from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings


def init_engine(app: FastAPI, settings: Settings) -> None:
    """Create engine + session factory; called from the lifespan startup."""
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,  # detect dead connections before handing them out
        echo=False,
    )
    app.state.db_engine = engine
    app.state.db_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


async def dispose_engine(app: FastAPI) -> None:
    """Close the pool cleanly; called from the lifespan shutdown."""
    await app.state.db_engine.dispose()


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """Session-per-request dependency.

    Commit-on-success / rollback-on-error lives here, in ONE place, so services
    and repositories never call commit() themselves — that's what keeps a
    request transactional (all writes land or none do).
    """
    session: AsyncSession
    async with request.app.state.db_sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
