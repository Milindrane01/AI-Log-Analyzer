"""Chat domain: one conversation per (user, log file) in v1."""

from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Timestamped, UUIDPrimaryKey


class Conversation(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("user_id", "log_file_id", name="uq_conv_user_file"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    log_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("log_files.id", ondelete="CASCADE"), index=True, nullable=False
    )


class Message(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "messages"

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True
    )  # [{start_line, end_line}]
