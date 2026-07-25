"""Ingestion + analysis wire formats."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models import AnalysisStatus, Severity


class PasteRequest(BaseModel):
    content: str = Field(min_length=1)
    filename: str = Field(default="pasted.log", max_length=255)


class AnalysisAccepted(BaseModel):
    """202 body: where to poll for the result."""

    analysis_id: str
    log_file_id: str
    status: AnalysisStatus


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    log_file_id: str
    status: AnalysisStatus
    error_message: str | None
    total_lines: int
    parsed_lines: int
    error_lines: int
    group_count: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class InsightResponse(BaseModel):
    """AI insight for a group. payload = schema-validated InsightResult fields."""

    model_config = ConfigDict(from_attributes=True)

    payload: dict[str, Any]
    model: str
    from_cache: bool


class ErrorGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fingerprint: str
    template: str
    level: str
    severity: Severity
    count: int
    first_seen: datetime | None
    last_seen: datetime | None
    sample_lines: list[str] | None
    insight: InsightResponse | None = None


class SimilarIncident(BaseModel):
    group_id: str
    analysis_id: str
    template: str
    severity: str
    score: float  # cosine similarity 0..1


class SimilarIncidentsResponse(BaseModel):
    enabled: bool  # false = similarity backend not configured
    items: list[SimilarIncident]


class AnalysisListItem(AnalysisResponse):
    filename: str


class AnalysisPage(BaseModel):
    items: list[AnalysisListItem]
    total: int
    limit: int
    offset: int


class ErrorGroupPage(BaseModel):
    items: list[ErrorGroupResponse]
    total: int
    limit: int
    offset: int
