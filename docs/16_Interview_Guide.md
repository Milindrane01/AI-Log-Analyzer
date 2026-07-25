# 16 — Interview Guide

## Overview

How to present this project in interviews: the narrative, the strongest talking points, per-module
explanations, trade-offs, and follow-up Q&A. Pairs with
[`docs/portfolio/interview-qa.md`](portfolio/interview-qa.md) and
[`docs/portfolio/system-design.md`](portfolio/system-design.md).

## The 60-second pitch

"An LLM-assisted incident-diagnosis platform. It fingerprints and groups errors *before* the model
sees them — so 212 identical timeouts cost one analysis, not 212 — grounds every AI answer in cited
evidence, suggests only allow-listed read-only commands, and runs a budgeted multi-agent
investigation for complex incidents. Full stack: FastAPI + Celery + React, Postgres/Redis/Qdrant,
Docker/Kubernetes, 99 tests that run offline."

## Per-module explanations (how to explain, why, trade-offs, follow-ups)

### Architecture — modular monolith
- **Explain:** one FastAPI codebase, two processes (api + worker), clean layers.
- **Why:** microservices solve org-scaling we don't have; seams allow later split ([ADR-001](adr/001-modular-monolith.md)).
- **Trade-off:** must enforce boundaries by review vs. compiler.
- **Follow-up:** "when split?" → worker needs independent release cadence / multiple teams.

### Async analysis — 202 + Celery
- **Why:** LLM calls take 10–60s; sync requests time out and duplicate cost ([ADR-002](adr/002-celery-for-ai-jobs.md)).
- **Follow-up:** "push vs poll?" → SSE (used for chat) or WebSockets; model unchanged.

### Deduplicate before the LLM
- **Why:** main cost + quality lever; fingerprinting = Sentry-style grouping.
- **Follow-up:** "accuracy cost of grouping?" → measurable ablation (research backlog).

### Grounded chat with code-level refusal
- **Why:** refuse below retrieval threshold *without an LLM call* → eliminates a class of
  hallucinations; citations for the rest.
- **Follow-up:** "prompt vs code guardrail?" → code first, prompt second.

### Allow-listed remediation
- **Why:** safety by construction — no template produces `rm -rf`; params regex-validated.
- **Follow-up:** "why not sanitize output?" → deny-by-default beats blocklists.

### Multi-agent investigation
- **Why:** for multi-service cascades; budgets + verifier + persisted trace make it defensible.
- **Follow-up:** "when NOT multi-agent?" → single errors, cheaper in one shot.

### Interface seams / offline tests
- **Why:** every dependency has a fake → 99 tests offline; caught real bugs deterministically.
- **Follow-up:** "show me" → `tests/conftest.py`, `MockLLMProvider`, `InlineTaskQueue`.

## System-design whiteboard prompts you can answer

- Draw the ingestion→analysis→poll flow ([04](04_Request_Flow.md)).
- Scale to 10× load (workers on queue depth; stateless API HPA; DB read replicas — [10](10_Performance_and_Scaling.md)).
- Threat-model log ingestion ([09](09_Security.md)).

## Strong example answers

See [`docs/portfolio/interview-qa.md`](portfolio/interview-qa.md) for full written answers to the
most common questions (modular monolith, async jobs, injection defense, liveness vs readiness,
tenant isolation, worker autoscaling, monitoring).

## Honest weaknesses to volunteer (shows maturity)

- In-memory rate limiter (needs Redis for multi-replica).
- Ephemeral RAG index (persist in Qdrant at scale).
- Rules-based agents (LLM agents are a drop-in via the `Agent` protocol).
- No evaluation on public benchmarks yet (the path to a paper — [18 FAQ](18_FAQ.md)).

## Interview notes

- Bring the [ERD](diagrams/erd.mmd) and [architecture](diagrams/architecture.mmd) diagrams; they
  answer half the questions before they're asked.
