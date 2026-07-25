"""Incident report + remediation command endpoints (M8)."""

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DBDep
from app.core.exceptions import DomainError, NotFoundError
from app.core.ratelimit import RateLimiter
from app.models import ErrorGroup
from app.models.insight import GroupInsight
from app.models.report import IncidentReport
from app.schemas.report import CommandsResponse, ReportResponse, SuggestedCommand
from app.services.pipeline import get_analysis_for_user
from app.services.report import generate_report

router = APIRouter(prefix="/analyses", tags=["reports"])


@router.post(
    "/{analysis_id}/report",
    response_model=ReportResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    summary="Generate (or regenerate) the incident report",
)
async def create_report(analysis_id: str, user: CurrentUser, session: DBDep) -> ReportResponse:
    analysis = await get_analysis_for_user(session, analysis_id, user.id)
    if analysis is None:
        raise NotFoundError("Analysis not found")
    if analysis.status.value != "completed":
        raise DomainError("Analysis is not complete yet")
    report = await generate_report(session, analysis)
    return ReportResponse.model_validate(report)


@router.get("/{analysis_id}/report", response_model=ReportResponse, summary="Get the report")
async def get_report(analysis_id: str, user: CurrentUser, session: DBDep) -> ReportResponse:
    if await get_analysis_for_user(session, analysis_id, user.id) is None:
        raise NotFoundError("Analysis not found")
    report = (
        await session.execute(
            select(IncidentReport).where(IncidentReport.analysis_id == analysis_id)
        )
    ).scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not generated yet")
    return ReportResponse.model_validate(report)


@router.get(
    "/{analysis_id}/report.md",
    response_class=PlainTextResponse,
    summary="Download the report as markdown",
)
async def download_report(analysis_id: str, user: CurrentUser, session: DBDep) -> PlainTextResponse:
    if await get_analysis_for_user(session, analysis_id, user.id) is None:
        raise NotFoundError("Analysis not found")
    report = (
        await session.execute(
            select(IncidentReport).where(IncidentReport.analysis_id == analysis_id)
        )
    ).scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not generated yet")
    return PlainTextResponse(
        report.markdown,
        headers={"Content-Disposition": f'attachment; filename="incident-{analysis_id}.md"'},
    )


@router.get(
    "/{analysis_id}/groups/{group_id}/commands",
    response_model=CommandsResponse,
    summary="Safe remediation commands for a group",
)
async def group_commands(
    analysis_id: str, group_id: str, user: CurrentUser, session: DBDep
) -> CommandsResponse:
    if await get_analysis_for_user(session, analysis_id, user.id) is None:
        raise NotFoundError("Analysis not found")
    group = await session.get(ErrorGroup, group_id)
    if group is None or group.analysis_id != analysis_id:
        raise NotFoundError("Group not found")
    insight = (
        await session.execute(select(GroupInsight).where(GroupInsight.group_id == group_id))
    ).scalar_one_or_none()
    error_type = insight.payload["error_type"] if insight else "Application Error"

    from app.ai.commands.selector import suggest_commands

    commands = [SuggestedCommand(**c) for c in suggest_commands(error_type)]
    return CommandsResponse(error_type=error_type, commands=commands)
