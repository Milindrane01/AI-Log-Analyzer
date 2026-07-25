"""Multi-agent investigation storage: the run + its full step trace.

Every agent step is persisted so the investigation is inspectable — no black
boxes. This is observability OF the AI system, the thing that makes multi-agent
defensible in production instead of a party trick.
"""

import enum
from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPrimaryKey


class InvestigationStatus(enum.StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Investigation(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "investigations"

    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    status: Mapped[InvestigationStatus] = mapped_column(
        String(16), default=InvestigationStatus.RUNNING, nullable=False
    )
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(default=0.0, nullable=False)
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    total_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class InvestigationStep(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "investigation_steps"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    agent: Mapped[str] = mapped_column(String(16), nullable=False)  # planner|investigator|verifier
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
