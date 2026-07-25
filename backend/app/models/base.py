"""Declarative base + shared column mixins."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Single metadata registry for every table in the app."""


class UUIDPrimaryKey:
    """UUID PKs: no enumeration attacks (/users/1, /users/2...), safe to expose,
    and generatable client-side. Stored as string for SQLite test compatibility."""

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))


class Timestamped:
    """created_at/updated_at maintained by the DB (server_default), not Python —
    correct even when rows are written outside the app."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
