"""Timeline + multi-agent investigation endpoints (M9)."""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import CurrentUser, DBDep
from app.core.exceptions import DomainError, NotFoundError
from app.core.ratelimit import RateLimiter
from app.models.investigation import Investigation, InvestigationStep
from app.schemas.investigation import (
    InvestigationResponse,
    InvestigationStepResponse,
    TimelineEventResponse,
    TimelineResponse,
)
from app.services.investigation import investigate
from app.services.pipeline import get_analysis_for_user
from app.services.timeline import build_timeline

router = APIRouter(prefix="/analyses", tags=["investigation"])


@router.get("/{analysis_id}/timeline", response_model=TimelineResponse, summary="Incident timeline")
async def get_timeline(analysis_id: str, user: CurrentUser, session: DBDep) -> TimelineResponse:
    analysis = await get_analysis_for_user(session, analysis_id, user.id)
    if analysis is None:
        raise NotFoundError("Analysis not found")
    events = await build_timeline(session, analysis)
    return TimelineResponse(events=[TimelineEventResponse(**asdict(e)) for e in events])


def _to_response(inv: Investigation, steps: list[InvestigationStep]) -> InvestigationResponse:
    return InvestigationResponse(
        id=inv.id,
        analysis_id=inv.analysis_id,
        status=inv.status if isinstance(inv.status, str) else inv.status.value,
        conclusion=inv.conclusion,
        confidence=inv.confidence,
        verified=inv.verified,
        total_steps=inv.total_steps,
        steps=[
            InvestigationStepResponse(seq=s.seq, agent=s.agent, action=s.action, content=s.content)
            for s in sorted(steps, key=lambda s: s.seq)
        ],
    )


@router.post(
    "/{analysis_id}/investigate",
    response_model=InvestigationResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    summary="Run a multi-agent investigation",
)
async def run(analysis_id: str, user: CurrentUser, session: DBDep) -> InvestigationResponse:
    analysis = await get_analysis_for_user(session, analysis_id, user.id)
    if analysis is None:
        raise NotFoundError("Analysis not found")
    if analysis.status.value != "completed":
        raise DomainError("Analysis is not complete yet")
    investigation = await investigate(session, analysis)
    steps = list(
        (
            await session.execute(
                select(InvestigationStep).where(
                    InvestigationStep.investigation_id == investigation.id
                )
            )
        ).scalars()
    )
    return _to_response(investigation, steps)


@router.get(
    "/{analysis_id}/investigation",
    response_model=InvestigationResponse,
    summary="Latest investigation for an analysis",
)
async def latest(analysis_id: str, user: CurrentUser, session: DBDep) -> InvestigationResponse:
    if await get_analysis_for_user(session, analysis_id, user.id) is None:
        raise NotFoundError("Analysis not found")
    inv = (
        await session.execute(
            select(Investigation)
            .where(Investigation.analysis_id == analysis_id)
            .order_by(Investigation.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if inv is None:
        raise NotFoundError("No investigation yet")
    steps = list(
        (
            await session.execute(
                select(InvestigationStep).where(InvestigationStep.investigation_id == inv.id)
            )
        ).scalars()
    )
    return _to_response(inv, steps)
