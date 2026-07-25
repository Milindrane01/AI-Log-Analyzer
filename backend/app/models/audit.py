"""Audit log: append-only record of security-relevant events.

Separate from application logging on purpose — logs rotate and get sampled;
audit rows are queryable evidence ("when did this account log in?").
"""

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPrimaryKey


class AuditLog(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "audit_logs"

    # Nullable: failed logins may have no known user.
    user_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)  # success | failure
    context: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)  # ip, email, …
