# Module 9 — Incident Timeline & Multi-Agent Investigation (Phases 9–10)

> **Status:** ✅ Built (2026-07-20) · 96/96 backend tests + frontend typecheck
> Depends on: Modules 4, 5, 7, 8 · Delivers AI Phases: 9 (timeline), 10 (multi-agent)

## As built — deviations from plan & key notes

- **Timeline is deterministic** (no LLM): groups carry first_seen/last_seen from M3 parsing;
  ordering by first occurrence turns "3 error piles" into a causal story. Earliest *timestamped*
  group is marked the first failure — the single most valuable incident signal.
- **Agents reason with rules, not prompts** (the significant deviation). This makes the
  investigation free, fast, fully testable, and reproducible while still demonstrating the
  multi-agent *architecture* (planner → investigator → verifier, an evidence toolbox, hard
  budgets, a persisted step trace) — which is the portfolio point. Each agent implements the
  `Agent` protocol, so an LLM-backed agent is a drop-in for richer narratives later.
- **The verifier earns its place**: it refuses to confirm causation without both a genuine
  earliest-failure AND a cascade — a single isolated error comes back `verified=false`
  ("correlation, not causation"), asserted in tests. That's the anti-hallucination check.
- **Hard budgets** (`MAX_STEPS`, `DEADLINE_SECONDS`) bound the loop — the canonical multi-agent
  failure is a runaway; exceeding budget ends gracefully with whatever was established.
- **Full trace persisted** (`investigation_steps`, migration 006): every agent step is
  inspectable in the UI — observability OF the AI system, which is what makes multi-agent
  defensible rather than a black box.
- Honest scope note in code: for most single-error analyses, M4's single-shot result is already
  the right tool; investigation is for multi-service cascades.

## Goal

The capstone. Complex incidents span services and time: reconstruct the causal chain
("redis pool exhausted at 10:11 → DB timeouts at 10:12 → 502s at 10:13") and run a structured
multi-agent investigation for incidents a single prompt can't crack.

## What gets built

- [x] Timeline builder: order groups causally by first occurrence, mark first-failure
- [x] `GET /analyses/{id}/timeline` + visual timeline UI (first-failure highlighted)
- [x] Multi-agent investigation with typed roles: Planner → Investigator → Verifier over an
      evidence toolbox (read-only views of the analyzed data)
- [x] Orchestration with hard budgets: MAX_STEPS + wall-clock deadline, graceful exit
- [x] Full trace persistence (migration 006): every step inspectable in the UI
- [x] Verifier fallback: no cascade → `verified=false`, "correlation not causation" caveat
- [x] Seeded cascade fixture (redis→DB→502) with known first-failure in tests

## Key concepts you'll learn

When multi-agent is worth it (and the strong case against it); orchestrator patterns vs
frameworks; tool-use loops with budgets as runaway-cost defense; verifier agents as
hallucination check; observability *of* AI systems (tracing agent decisions).

## Planned files

`app/ai/agents/{planner,investigator,verifier}.py`, `app/ai/agents/orchestrator.py`,
`app/services/timeline.py`, `app/api/v1/timeline.py`, `frontend/src/pages/Timeline.tsx`

## Acceptance criteria (demo)

A seeded 3-service cascade log → timeline correctly identifies redis as first failure; the
investigation trace shows planner → investigators → verifier reasoning; total cost stays under
the configured budget.
