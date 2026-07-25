"""Log ingestion domain: LogFile → Analysis → ErrorGroups.

Design note (deviation from the original outline): there is no LogEntry table.
Persisting 1M rows per 50MB file would bloat postgres for little value — groups
carry representative sample lines (JSON), and the raw file stays on disk for
M7's RAG chunking to re-read. Documented in module-03 doc.
"""

import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, Timestamped, UUIDPrimaryKey


class AnalysisStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(enum.StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LogFile(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "log_files"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # sha256
    source: Mapped[str] = mapped_column(String(16), nullable=False)  # upload | paste
    detected_format: Mapped[str | None] = mapped_column(String(32), nullable=True)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="log_file")


class Analysis(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "analyses"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    log_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("log_files.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, native_enum=False, length=16),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)  # why FAILED
    total_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parsed_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_lines: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    group_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    log_file: Mapped[LogFile] = relationship(back_populates="analyses")
    groups: Mapped[list["ErrorGroup"]] = relationship(back_populates="analysis")


class ErrorGroup(Base, UUIDPrimaryKey, Timestamped):
    __tablename__ = "error_groups"

    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    fingerprint: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)  # normalized message
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, native_enum=False, length=16), nullable=False
    )
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sample_lines: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # up to 5 raw lines

    analysis: Mapped[Analysis] = relationship(back_populates="groups")
