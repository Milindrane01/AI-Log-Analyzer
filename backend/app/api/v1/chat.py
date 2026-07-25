"""Chat-with-logs endpoints: history (JSON) + ask (SSE stream).

SSE events: {"type":"token","text":...}* then {"type":"done","message_id":...,"citations":[...]}
The frontend consumes this with fetch + ReadableStream (EventSource can't send
Authorization headers — a classic SSE gotcha).
"""

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBDep
from app.core.exceptions import DomainError, NotFoundError
from app.core.ratelimit import RateLimiter
from app.models import Conversation, LogFile, Message
from app.schemas.chat import ChatHistory, ChatMessage, ChatRequest

router = APIRouter(prefix="/logs", tags=["chat"])


class AIUnavailableError(DomainError):
    status_code = 503
    code = "ai_unavailable"


async def _get_file(session: AsyncSession, log_file_id: str, user_id: str) -> LogFile:
    log_file = await session.get(LogFile, log_file_id)
    if log_file is None or log_file.user_id != user_id:
        raise NotFoundError("Log file not found")
    return log_file


async def _get_or_create_conversation(
    session: AsyncSession, user_id: str, log_file_id: str
) -> Conversation:
    conv = (
        await session.execute(
            select(Conversation).where(
                Conversation.user_id == user_id, Conversation.log_file_id == log_file_id
            )
        )
    ).scalar_one_or_none()
    if conv is None:
        conv = Conversation(user_id=user_id, log_file_id=log_file_id)
        session.add(conv)
        await session.flush()
    return conv


@router.get("/{log_file_id}/chat", response_model=ChatHistory, summary="Conversation history")
async def chat_history(log_file_id: str, user: CurrentUser, session: DBDep) -> ChatHistory:
    await _get_file(session, log_file_id, user.id)
    conv = await _get_or_create_conversation(session, user.id, log_file_id)
    rows = (
        await session.execute(
            select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
        )
    ).scalars()
    return ChatHistory(conversation_id=conv.id, items=[ChatMessage.model_validate(m) for m in rows])


@router.post(
    "/{log_file_id}/chat",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
    summary="Ask a question about this log (SSE stream)",
)
async def chat_ask(
    log_file_id: str,
    body: ChatRequest,
    request: Request,
    user: CurrentUser,
    session: DBDep,
) -> StreamingResponse:
    provider = getattr(request.app.state, "llm_provider", None)
    embedder = request.app.state.embedder
    if provider is None or embedder is None:
        raise AIUnavailableError("AI chat requires an OpenAI API key (APP_OPENAI_API_KEY)")

    log_file = await _get_file(session, log_file_id, user.id)
    conv = await _get_or_create_conversation(session, user.id, log_file_id)

    history_rows = (
        await session.execute(
            select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
        )
    ).scalars()
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    session.add(Message(conversation_id=conv.id, role="user", content=body.message))
    await session.commit()  # user message survives even if the stream dies

    async def event_stream() -> AsyncIterator[str]:
        from app.ai.pipelines.chat import ChatResult, stream_chat_answer

        result = ChatResult()
        try:
            async for token in stream_chat_answer(
                provider, embedder, log_file.storage_path, history, body.message, result
            ):
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        except Exception:  # provider/stream failure → explicit error event, not silence
            yield f"data: {json.dumps({'type': 'error', 'message': 'Chat failed, try again'})}\n\n"
            return
        assistant = Message(
            conversation_id=conv.id,
            role="assistant",
            content=result.answer,
            citations=result.citations,
        )
        session.add(assistant)
        await session.commit()
        done = {"type": "done", "message_id": assistant.id, "citations": result.citations}
        yield f"data: {json.dumps(done)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
