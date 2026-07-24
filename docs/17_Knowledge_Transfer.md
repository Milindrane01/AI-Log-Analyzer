# 17 — Knowledge Transfer

## Overview

Everything an incoming engineer/team needs to own this system: mental model, where things live,
operational responsibilities, gotchas, and open work. This is the production-handover document.

## Mental model in five sentences

1. Users upload/paste logs; the API stores them and returns `202`, doing heavy work asynchronously.
2. A Celery worker (same image) detects format, parses, **fingerprints and groups** errors, then
   optionally enriches the top groups with an LLM and indexes them for similarity search.
3. Everything AI is behind an **interface with a fake**, so the whole system runs and tests offline.
4. Log content is **untrusted** — it's fenced as data, and remediation commands come from an
   **allow-listed catalog** (read-only, never executed).
5. Auth is JWT; data is per-user isolated; the app is observable via `/metrics` and health probes.

## Where things live (fast index)

| I need to… | Go to |
|---|---|
| Change a setting | `backend/app/core/config.py` (+ `.env.example`) |
| Add/modify an endpoint | `backend/app/api/v1/` + `schemas/` + `services/` |
| Change parsing/grouping | `backend/app/parsing/` |
| Change AI behavior | `backend/app/ai/` (providers, prompts, guards, rag, agents, commands) |
| Change the pipeline | `backend/app/services/pipeline.py` |
| Add a table | `backend/app/models/` + `alembic/versions/` |
| Change the UI | `frontend/src/` |
| Change deploy | `docker-compose.yml`, `infra/k8s/`, `infra/docker/` |
| Understand a past decision | `docs/adr/`, `docs/modules/` |

## Ownership & responsibilities (Inference — assign on handover)

| Area | Typical owner |
|---|---|
| Backend/API | Backend engineer |
| AI pipeline & prompts | AI engineer |
| Infra/CI/CD/monitoring | DevOps/SRE |
| Frontend | Frontend engineer |
| DB & migrations | Backend/DBA |

## System boundaries & external dependencies

- **OpenAI** (optional) — behind `LLMProvider`; outage degrades gracefully.
- **Qdrant** (optional) — behind `VectorStore`; empty URL disables similarity.
- **Redis** — Celery broker (+ future rate-limit store).
- **PostgreSQL** — system of record.

## Non-obvious gotchas (read before touching code)

- **Commit before enqueue** in ingestion (`api/v1/logs.py`) — otherwise the worker races the write.
- **Liveness vs readiness** are intentionally different — don't add a DB check to liveness.
- **The worker is the same image**, different command — deploy them together.
- **Metrics paths are templated** — don't add raw IDs to labels (cardinality).
- **Parser registry order** — `PlainParser` must stay last (fallback).
- **Prod refuses the dev JWT secret** — set `APP_JWT_SECRET_KEY`.

## Build history & rationale

The system was built in 11 milestones (M0–M10), each with an "as-built" doc in `docs/modules/`
documenting deviations and trade-offs; decisions are in `docs/adr/`; the full log is in
[`progress.md`](../progress.md).

## Open work / backlog (what to do next)

Prioritized in [`docs/planning/05-backlog.md`](planning/05-backlog.md). Highest value:
Redis-backed rate limiter + refresh denylist; frontend component tests; worker queue-depth
autoscaling; transactional outbox; PDF export; persisted RAG index.

## Handover checklist

- [ ] Access to repo, cloud project, secrets vault, OpenAI billing, Grafana.
- [ ] Run `bash scripts/setup.sh`; confirm 99 tests pass locally.
- [ ] `docker compose up --build`; walk the [User Guide](15_User_Guide.md) end to end.
- [ ] Review [ADRs](adr/) and the [risk register](planning/04-risk-register.md).
- [ ] Confirm production env vars (esp. `APP_JWT_SECRET_KEY`) and backups.

## Interview notes

- **KT in one line:** "Interfaces + fakes make it understandable and safe to change; every decision
  has an ADR."
