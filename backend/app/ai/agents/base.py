"""Agent contracts + the evidence tools agents are allowed to use.

Agents don't get raw model access to do anything — they get a fixed TOOLBOX of
read-only evidence lookups over the already-analyzed data. This bounds what an
investigation can do and keeps every step reproducible/inspectable.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class Evidence:
    """Read-only view of the analysis an investigation reasons over."""

    timeline: list[dict[str, Any]]  # ordered events (from services.timeline)
    groups: list[dict[str, Any]]  # error groups with insights
    first_failure: dict[str, Any] | None


@dataclass(slots=True)
class Step:
    agent: str
    action: str
    content: dict[str, Any]


@dataclass(slots=True)
class InvestigationOutcome:
    conclusion: str
    confidence: float
    verified: bool
    steps: list[Step] = field(default_factory=list)


class Agent(Protocol):
    name: str

    def run(self, evidence: Evidence, scratch: dict[str, Any]) -> Step:
        """Do one bounded unit of work; append findings to `scratch`."""
        ...
