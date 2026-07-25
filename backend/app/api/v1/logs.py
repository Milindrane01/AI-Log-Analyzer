"""Log ingestion endpoints — 202 Accepted pattern (ADR-002)."""

from fastapi import APIRouter, Depends, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBDep, SettingsDep
from app.core.ratelimit import RateLimiter
from app.models import Analysis
from app.schemas.logs import AnalysisAccepted, PasteRequest
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/logs", tags=["logs"])


async def _accept(request: Request, session: AsyncSession, analysis: Analysis) -> AnalysisAccepted:
    # COMMIT BEFORE ENQUEUE. The worker opens its own session; if we enqueue
    # inside an uncommitted transaction, the worker races ahead and finds
    # nothing (a classic async-job bug — our tests caught it live).
    await session.commit()
    await request.app.state.task_queue.enqueue_analysis(analysis.id)
    return AnalysisAccepted(
        analysis_id=analysis.id, log_file_id=analysis.log_file_id, status=analysis.status
    )


@router.post(
    "",
    response_model=AnalysisAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    summary="Upload a log file for analysis",
)
async def upload_log(
    request: Request,
    file: UploadFile,
    user: CurrentUser,
    session: DBDep,
    settings: SettingsDep,
) -> AnalysisAccepted:
    analysis = await IngestionService(session, settings).ingest_upload(user.id, file)
    return await _accept(request, session, analysis)


@router.post(
    "/paste",
    response_model=AnalysisAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
    summary="Paste raw log text for analysis",
)
async def paste_log(
    request: Request,
    body: PasteRequest,
    user: CurrentUser,
    session: DBDep,
    settings: SettingsDep,
) -> AnalysisAccepted:
    analysis = await IngestionService(session, settings).ingest_paste(
        user.id, body.content, body.filename
    )
    return await _accept(request, session, analysis)
