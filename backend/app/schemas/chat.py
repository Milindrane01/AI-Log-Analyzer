"""Chat wire formats."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    citations: list[dict] | None
    created_at: datetime


class ChatHistory(BaseModel):
    conversation_id: str
    items: list[ChatMessage]
