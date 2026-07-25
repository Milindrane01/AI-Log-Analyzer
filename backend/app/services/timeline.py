"""Incident timeline: reconstruct the causal story from grouped errors.

Deterministic — no LLM. Each error group carries first_seen/last_seen from
parsing (M3); ordering those by first occurrence turns "3 unrelated error
piles" into "redis degraded at 10:11 → DB timeouts at 10:12 → 502s at 10:13".
The FIRST failure is the most valuable signal in any incident, so it's marked.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Analysis, ErrorGroup

_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass(slots=True)
class TimelineEvent:
    group_id: str
    label: str  # error_type if known else template
    severity: str
    count: int
    first_seen: datetime | None
    last_seen: datetime | None
    is_first_failure: bool


async def build_timeline(session: AsyncSession, analysis: Analysis) -> list[TimelineEvent]:
    """Return groups ordered by first occurrence; mark the earliest as first failure."""
    from app.models.insight import GroupInsight

    groups = list(
        (
            await session.execute(select(ErrorGroup).where(ErrorGroup.analysis_id == analysis.id))
        ).scalars()
    )
    if not groups:
        return []

    insights = {
        i.group_id: i.payload.get("error_type")
        for i in (
            await session.execute(
                select(GroupInsight).where(GroupInsight.group_id.in_([g.id for g in groups]))
            )
        ).scalars()
    }

    def sort_key(g: ErrorGroup) -> tuple[bool, datetime, int, int]:
        # Timestamped groups first (by time); undated groups fall back to
        # severity then count so the ordering is still deterministic.
        return (
            g.first_seen is None,
            g.first_seen or datetime.max,
            _SEVERITY_RANK.get(g.severity.value, 9),
            -g.count,
        )

    ordered = sorted(groups, key=sort_key)
    # First failure = earliest *timestamped* group if any, else the first ordered.
    dated = [g for g in ordered if g.first_seen is not None]
    first_failure_id = (dated[0] if dated else ordered[0]).id

    return [
        TimelineEvent(
            group_id=g.id,
            label=insights.get(g.id) or g.template,
            severity=g.severity.value,
            count=g.count,
            first_seen=g.first_seen,
            last_seen=g.last_seen,
            is_first_failure=(g.id == first_failure_id),
        )
        for g in ordered
    ]
