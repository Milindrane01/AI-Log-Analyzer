"""Incident report + command wire formats."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    analysis_id: str
    title: str
    markdown: str
    created_at: datetime


class SuggestedCommand(BaseModel):
    command: str
    description: str
    domain: str


class CommandsResponse(BaseModel):
    error_type: str
    commands: list[SuggestedCommand]
