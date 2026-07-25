"""Analysis status + results endpoints (the polling half of the 202 pattern)."""

from typing import Annotated

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBDep
from app.core.exceptions import NotFoundError
from app.models import Analysis, ErrorGroup, LogFile
from app.models.insight import GroupInsight
from app.schemas.logs import (
    AnalysisListItem,
    AnalysisPage,
    AnalysisResponse,
    ErrorGroupPage,
    ErrorGroupResponse,
    InsightResponse,
    SimilarIncident,
    SimilarIncidentsResponse,
)
from app.services.pipeline import get_analysis_for_user

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.get("", response_model=AnalysisPage, summary="Analysis history (newest first)")
async def list_analyses(
    user: CurrentUser,
    session: DBDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalysisPage:
    total = await session.scalar(
        select(func.count()).select_from(Analysis).where(Analysis.user_id == user.id)
    )
    rows = await session.execute(
        select(Analysis, LogFile.filename)
        .join(LogFile, Analysis.log_file_id == LogFile.id)
        .where(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [
        AnalysisListItem(**AnalysisResponse.model_validate(a).model_dump(), filename=fname)
        for a, fname in rows.all()
    ]
    return AnalysisPage(items=items, total=total or 0, limit=limit, offset=offset)


@router.get(
    "/{analysis_id}/similar",
    response_model=SimilarIncidentsResponse,
    summary="Similar past incidents ('have we seen this before?')",
)
async def similar_incidents(
    analysis_id: str,
    request: Request,
    user: CurrentUser,
    session: DBDep,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
) -> SimilarIncidentsResponse:
    if await get_analysis_for_user(session, analysis_id, user.id) is None:
        raise NotFoundError("Analysis not found")
    embedder = request.app.state.embedder
    store = request.app.state.vector_store
    if embedder is None or store is None:
        return SimilarIncidentsResponse(enabled=False, items=[])

    from app.services.similarity import find_similar

    top_groups = (
        (
            await session.execute(
                select(ErrorGroup)
                .where(ErrorGroup.analysis_id == analysis_id)
                .order_by(ErrorGroup.count.desc())
                .limit(3)  # similar search on the top groups only
            )
        )
        .scalars()
        .all()
    )

    seen: set[str] = set()
    items: list[SimilarIncident] = []
    for group in top_groups:
        for match in await find_similar(
            embedder, store, group, user.id, exclude_analysis_id=analysis_id, limit=limit
        ):
            if match["group_id"] in seen:
                continue
            seen.add(match["group_id"])
            items.append(SimilarIncident(**match))
    items.sort(key=lambda i: i.score, reverse=True)
    return SimilarIncidentsResponse(enabled=True, items=items[:limit])


@router.get("/{analysis_id}", response_model=AnalysisResponse, summary="Analysis status")
async def get_analysis(analysis_id: str, user: CurrentUser, session: DBDep) -> AnalysisResponse:
    analysis = await get_analysis_for_user(session, analysis_id, user.id)
    if analysis is None:  # includes other users' analyses: 404, never 403 (no existence leak)
        raise NotFoundError("Analysis not found")
    return AnalysisResponse.model_validate(analysis)


@router.get(
    "/{analysis_id}/groups",
    response_model=ErrorGroupPage,
    summary="Error groups, most frequent first",
)
async def list_groups(
    analysis_id: str,
    user: CurrentUser,
    session: DBDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ErrorGroupPage:
    if await get_analysis_for_user(session, analysis_id, user.id) is None:
        raise NotFoundError("Analysis not found")

    total = await session.scalar(
        select(func.count()).select_from(ErrorGroup).where(ErrorGroup.analysis_id == analysis_id)
    )
    result = await session.execute(
        select(ErrorGroup)
        .where(ErrorGroup.analysis_id == analysis_id)
        .order_by(ErrorGroup.count.desc())
        .limit(limit)
        .offset(offset)
    )
    groups = list(result.scalars())

    insights_by_group: dict[str, GroupInsight] = {}
    if groups:
        insight_rows = await session.execute(
            select(GroupInsight).where(GroupInsight.group_id.in_([g.id for g in groups]))
        )
        insights_by_group = {i.group_id: i for i in insight_rows.scalars()}

    items = []
    for g in groups:
        item = ErrorGroupResponse.model_validate(g)
        insight = insights_by_group.get(g.id)
        if insight is not None:
            item.insight = InsightResponse.model_validate(insight)
        items.append(item)
    return ErrorGroupPage(items=items, total=total or 0, limit=limit, offset=offset)
