"""Concrete agents. Deterministic reasoning over evidence — no LLM required.

Design choice (deviation worth defending): M9's agents reason with rules, not
prompts. This makes the investigation FREE, fast, fully testable, and
reproducible — and it still demonstrates the multi-agent *architecture*
(planner/investigator/verifier, tools, budgets, trace) which is the portfolio
point. An LLM-backed agent implements the same `Agent` protocol as a drop-in
when you want richer narratives (documented in module doc)."""

from typing import Any

from app.ai.agents.base import Agent, Evidence, Step

_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class PlannerAgent:
    name = "planner"

    def run(self, evidence: Evidence, scratch: dict[str, Any]) -> Step:
        # Decompose: what do we need to establish? Prioritize the first failure
        # and the highest-severity groups.
        subjects = [evidence.first_failure] if evidence.first_failure else []
        subjects += [
            g
            for g in evidence.groups
            if not evidence.first_failure or g["group_id"] != evidence.first_failure["group_id"]
        ]
        plan = [s["label"] for s in subjects[:5] if s]
        scratch["plan"] = plan
        scratch["subjects"] = subjects[:5]
        return Step("planner", "plan", {"questions": plan, "event_count": len(evidence.timeline)})


class InvestigatorAgent:
    name = "investigator"

    def run(self, evidence: Evidence, scratch: dict[str, Any]) -> Step:
        # Build a causal hypothesis: earliest failure is the likely trigger;
        # later higher-or-equal severity groups are candidate downstream effects.
        first = evidence.first_failure
        findings: list[str] = []
        if first is not None:
            findings.append(f"First observed failure: {first['label']} ({first['count']}×).")
            downstream = [
                e["label"] for e in evidence.timeline if e["group_id"] != first["group_id"]
            ]
            if downstream:
                findings.append(
                    "Likely downstream effects, in order: " + " → ".join(downstream[:4]) + "."
                )
            hypothesis = (
                f"{first['label']} was the trigger; the remaining errors are cascade effects."
                if downstream
                else f"{first['label']} is an isolated failure."
            )
        else:
            hypothesis = (
                "No timestamped ordering available; treating the highest-severity group as primary."
            )
            top = min(
                evidence.groups, key=lambda g: _SEVERITY_RANK.get(g["severity"], 9), default=None
            )
            if top:
                findings.append(f"Highest-severity group: {top['label']}.")
        scratch["hypothesis"] = hypothesis
        scratch["findings"] = findings
        return Step("investigator", "hypothesis", {"hypothesis": hypothesis, "findings": findings})


class VerifierAgent:
    name = "verifier"

    def run(self, evidence: Evidence, scratch: dict[str, Any]) -> Step:
        # Challenge the hypothesis against the evidence. Verified only if the
        # first failure is genuinely the earliest AND there is a cascade to explain.
        first = evidence.first_failure
        dated = [e for e in evidence.timeline if e["first_seen"]]
        supported = first is not None and (not dated or dated[0]["group_id"] == first["group_id"])
        has_cascade = len(evidence.timeline) > 1
        verified = supported and has_cascade
        confidence = 0.85 if verified else (0.6 if first else 0.4)
        note = (
            "Ordering confirms the trigger precedes the cascade."
            if verified
            else "Insufficient temporal evidence to confirm causation; treat as correlation."
        )
        scratch["verified"] = verified
        scratch["confidence"] = confidence
        scratch["verifier_note"] = note
        return Step(
            "verifier", "verify", {"verified": verified, "confidence": confidence, "note": note}
        )


def default_agents() -> list[Agent]:
    return [PlannerAgent(), InvestigatorAgent(), VerifierAgent()]
