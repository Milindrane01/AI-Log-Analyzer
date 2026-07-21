"""Multi-agent orchestrator: budgets, roles, verification logic."""

from app.ai.agents.base import Evidence
from app.ai.agents.orchestrator import MAX_STEPS, run_investigation


def _cascade_evidence() -> Evidence:
    timeline = [
        {"group_id": "g1", "label": "Redis pool exhausted", "severity": "high",
         "count": 38, "first_seen": "2026-07-15T10:11:00", "is_first_failure": True},
        {"group_id": "g2", "label": "Database Connectivity", "severity": "critical",
         "count": 212, "first_seen": "2026-07-15T10:12:00", "is_first_failure": False},
        {"group_id": "g3", "label": "HTTP 502", "severity": "high",
         "count": 500, "first_seen": "2026-07-15T10:13:00", "is_first_failure": False},
    ]
    return Evidence(timeline=timeline, groups=timeline, first_failure=timeline[0])


def test_investigation_runs_three_agents_in_order() -> None:
    outcome = run_investigation(_cascade_evidence())

    agents = [s.agent for s in outcome.steps]
    assert agents == ["planner", "investigator", "verifier"]


def test_identifies_first_failure_as_trigger() -> None:
    outcome = run_investigation(_cascade_evidence())

    assert "Redis pool exhausted" in outcome.conclusion
    assert "trigger" in outcome.conclusion.lower()
    assert outcome.verified is True
    assert outcome.confidence >= 0.8


def test_step_trace_is_inspectable() -> None:
    outcome = run_investigation(_cascade_evidence())

    planner = next(s for s in outcome.steps if s.agent == "planner")
    assert "questions" in planner.content
    verifier = next(s for s in outcome.steps if s.agent == "verifier")
    assert "verified" in verifier.content and "note" in verifier.content


def test_single_error_is_not_falsely_verified() -> None:
    single = [{"group_id": "g1", "label": "Disk full", "severity": "high", "count": 3,
               "first_seen": "2026-07-15T10:00:00", "is_first_failure": True}]
    outcome = run_investigation(Evidence(timeline=single, groups=single, first_failure=single[0]))

    assert outcome.verified is False  # no cascade → correlation, not causation
    assert "isolated" in outcome.conclusion.lower()


def test_no_evidence_degrades_gracefully() -> None:
    outcome = run_investigation(Evidence(timeline=[], groups=[], first_failure=None))

    assert outcome.verified is False
    assert outcome.steps  # still produced a trace, didn't crash


def test_budget_is_never_exceeded() -> None:
    outcome = run_investigation(_cascade_evidence())
    assert len(outcome.steps) <= MAX_STEPS
