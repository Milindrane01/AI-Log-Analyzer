"""Analysis pipeline: detect format → parse → fingerprint/group → persist.

Runs OUTSIDE the request cycle (Celery worker, or inline in tests). Owns its
own session/transaction because there is no request to attach to.
"""

from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Analysis, AnalysisStatus, ErrorGroup, LogFile, Severity
from app.parsing import detector
from app.parsing.fingerprint import fingerprint

log = structlog.get_logger()

# Only WARNING+ becomes an error group; info/debug noise stays out of the DB.
_GROUPED_LEVELS = {"warning", "error", "critical"}
_SEVERITY_BY_LEVEL = {
    "critical": Severity.CRITICAL,
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
}
MAX_SAMPLES_PER_GROUP = 5


class _GroupAccumulator:
    """In-memory aggregation while streaming the file — one DB write per group at the end."""

    __slots__ = ("count", "first_seen", "last_seen", "level", "samples", "template")

    def __init__(self, level: str, template: str) -> None:
        self.level = level
        self.template = template
        self.count = 0
        self.first_seen: datetime | None = None
        self.last_seen: datetime | None = None
        self.samples: list[str] = []

    def add(self, raw: str, timestamp: datetime | None) -> None:
        self.count += 1
        if len(self.samples) < MAX_SAMPLES_PER_GROUP:
            self.samples.append(raw[:2000])
        if timestamp is not None:
            if self.first_seen is None or timestamp < self.first_seen:
                self.first_seen = timestamp
            if self.last_seen is None or timestamp > self.last_seen:
                self.last_seen = timestamp


async def run_analysis(
    analysis_id: str,
    sessionmaker: async_sessionmaker,
    provider=None,  # LLMProvider | None — None = AI disabled, groups only
    embedder=None,  # EmbeddingProvider | None
    vector_store=None,  # VectorStore | None — both set = similarity indexing on
) -> None:
    """Execute one analysis end-to-end. Any exception → status FAILED (never lost)."""
    async with sessionmaker() as session:
        analysis = await session.get(Analysis, analysis_id)
        if analysis is None:
            log.error("analysis_not_found", analysis_id=analysis_id)
            return
        log_file = await session.get(LogFile, analysis.log_file_id)

        analysis.status = AnalysisStatus.RUNNING
        analysis.started_at = datetime.now(timezone.utc)
        await session.commit()

        try:
            stats = await _process(session, analysis, log_file, provider, embedder, vector_store)
            analysis.status = AnalysisStatus.COMPLETED
            analysis.total_lines, analysis.parsed_lines, analysis.error_lines, analysis.group_count = stats
        except Exception as exc:
            log.error("analysis_failed", analysis_id=analysis_id, exc_info=True)
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(exc)[:2000]
        analysis.finished_at = datetime.now(timezone.utc)
        await session.commit()
        log.info("analysis_finished", analysis_id=analysis_id, status=analysis.status.value)


async def _process(
    session,
    analysis: Analysis,
    log_file: LogFile,
    provider=None,
    embedder=None,
    vector_store=None,
) -> tuple[int, int, int, int]:
    with open(log_file.storage_path, encoding="utf-8", errors="replace") as fh:
        head = [fh.readline() for _ in range(detector.SAMPLE_SIZE)]
        parser = detector.detect(head)
        fh.seek(0)

        groups: dict[str, _GroupAccumulator] = {}
        total = parsed = errors = 0
        for line in fh:
            if not line.strip():
                continue
            total += 1
            entry = parser.parse_line(line)
            if entry is None:
                continue
            parsed += 1
            if entry.level not in _GROUPED_LEVELS:
                continue
            errors += 1
            digest, template = fingerprint(entry.level, entry.message)
            acc = groups.get(digest)
            if acc is None:
                acc = groups[digest] = _GroupAccumulator(entry.level, template)
            acc.add(entry.raw, entry.timestamp)

    log_file.detected_format = parser.name
    for digest, acc in groups.items():
        session.add(
            ErrorGroup(
                analysis_id=analysis.id,
                fingerprint=digest,
                template=acc.template,
                level=acc.level,
                severity=_SEVERITY_BY_LEVEL[acc.level],
                count=acc.count,
                first_seen=acc.first_seen,
                last_seen=acc.last_seen,
                sample_lines=acc.samples,
            )
        )
    await session.flush()

    if provider is not None and groups:
        from app.ai.pipelines.analyze import enrich_groups
        from app.core.config import get_settings

        persisted = (
            await session.execute(
                select(ErrorGroup).where(ErrorGroup.analysis_id == analysis.id)
            )
        ).scalars().all()
        written = await enrich_groups(
            session,
            provider,
            list(persisted),
            analysis.user_id,
            log_file.detected_format,
            get_settings().ai_max_groups_per_analysis,
        )
        log.info("ai_enrichment_done", analysis_id=analysis.id, insights=written)

    if embedder is not None and vector_store is not None and groups:
        from app.services.similarity import index_groups

        persisted = (
            await session.execute(
                select(ErrorGroup).where(ErrorGroup.analysis_id == analysis.id)
            )
        ).scalars().all()
        try:
            await index_groups(
                embedder, vector_store, list(persisted), analysis.user_id, analysis.id
            )
        except Exception:
            log.warning("similarity_indexing_failed", analysis_id=analysis.id, exc_info=True)

    return total, parsed, errors, len(groups)


async def get_analysis_for_user(session, analysis_id: str, user_id: str) -> Analysis | None:
    result = await session.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
    )
    return result.scalar_one_or_none()
