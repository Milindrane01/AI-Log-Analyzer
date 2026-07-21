"""AI insight storage: one insight per error group.

The payload is the schema-validated InsightResult as JSON — storing it whole
keeps the DB schema stable while prompt output evolves. Token counts make cost
per analysis queryable (FinOps from day one).
"""

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPrimaryKey


class GroupInsight(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "group_insights"

    group_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("error_groups.id", ondelete="CASCADE"),
        unique=True, index=True, nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # cache key
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)  # InsightResult.model_dump()
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    from_cache: Mapped[bool] = mapped_column(default=False, nullable=False)
