"""Timeline + investigation wire formats."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TimelineEventResponse(BaseModel):
    group_id: str
    label: str
    severity: str
    count: int
    first_seen: datetime | None
    last_seen: datetime | None
    is_first_failure: bool


class TimelineResponse(BaseModel):
    events: list[TimelineEventResponse]


class InvestigationStepResponse(BaseModel):
    seq: int
    agent: str
    action: str
    content: dict[str, Any]


class InvestigationResponse(BaseModel):
    id: str
    analysis_id: str
    status: str
    conclusion: str | None
    confidence: float
    verified: bool
    total_steps: int
    steps: list[InvestigationStepResponse]
