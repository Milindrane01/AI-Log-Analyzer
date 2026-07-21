"""Run and persist a multi-agent investigation over an analysis."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.base import Evidence
from app.ai.agents.orchestrator import run_investigation
from app.models import Analysis
from app.models.investigation import Investigation, InvestigationStatus, InvestigationStep
from app.services.timeline import build_timeline


async def investigate(session: AsyncSession, analysis: Analysis) -> Investigation:
    """Build evidence from the analysis, run the agent loop, persist the trace."""
    events = await build_timeline(session, analysis)
    timeline = [
        {
            "group_id": e.group_id,
            "label": e.label,
            "severity": e.severity,
            "count": e.count,
            "first_seen": e.first_seen.isoformat() if e.first_seen else None,
            "is_first_failure": e.is_first_failure,
        }
        for e in events
    ]
    first = next((e for e in timeline if e["is_first_failure"]), None)
    evidence = Evidence(timeline=timeline, groups=timeline, first_failure=first)

    outcome = run_investigation(evidence)

    investigation = Investigation(
        analysis_id=analysis.id,
        user_id=analysis.user_id,
        status=InvestigationStatus.COMPLETED,
        conclusion=outcome.conclusion,
        confidence=outcome.confidence,
        verified=outcome.verified,
        total_steps=len(outcome.steps),
    )
    session.add(investigation)
    await session.flush()

    for seq, step in enumerate(outcome.steps):
        session.add(
            InvestigationStep(
                investigation_id=investigation.id,
                seq=seq,
                agent=step.agent,
                action=step.action,
                content=step.content,
            )
        )
    await session.flush()
    return investigation
