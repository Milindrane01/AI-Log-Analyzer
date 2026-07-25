"""Audit log writes — append-only, no update/delete methods on purpose."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        action: str,
        outcome: str,
        user_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._session.add(
            AuditLog(action=action, outcome=outcome, user_id=user_id, context=context)
        )
        await self._session.flush()
