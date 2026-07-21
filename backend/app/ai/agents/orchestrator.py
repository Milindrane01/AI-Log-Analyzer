"""Investigation orchestrator: run the agent loop under hard budgets.

Budgets are the whole point of safe agent systems: a runaway loop is the
canonical multi-agent failure. MAX_STEPS and a wall-clock deadline bound cost
and latency; exceeding either ends the investigation with whatever was
established so far (graceful, never hanging).
"""

import time

from app.ai.agents.agents import default_agents
from app.ai.agents.base import Evidence, InvestigationOutcome, Step

MAX_STEPS = 8
DEADLINE_SECONDS = 20.0


def run_investigation(evidence: Evidence) -> InvestigationOutcome:
    """Execute planner → investigator → verifier within budget; assemble the outcome."""
    agents = default_agents()
    scratch: dict = {}
    steps: list[Step] = []
    started = time.monotonic()

    for agent in agents:
        if len(steps) >= MAX_STEPS or (time.monotonic() - started) > DEADLINE_SECONDS:
            steps.append(Step("orchestrator", "budget_exceeded", {"steps": len(steps)}))
            break
        steps.append(agent.run(evidence, scratch))

    hypothesis = scratch.get("hypothesis", "No hypothesis could be formed from the evidence.")
    verifier_note = scratch.get("verifier_note", "")
    conclusion = hypothesis + (f" {verifier_note}" if verifier_note else "")

    return InvestigationOutcome(
        conclusion=conclusion,
        confidence=scratch.get("confidence", 0.4),
        verified=scratch.get("verified", False),
        steps=steps,
    )
