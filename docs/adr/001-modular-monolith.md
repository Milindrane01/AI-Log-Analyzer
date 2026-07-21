# ADR-001: Build a modular monolith, not microservices

- **Status:** Accepted
- **Date:** 2026-07-16
- **Deciders:** TG

## Context

The platform has multiple concerns (auth, ingestion, parsing, AI analysis, search, chat) that
could each be a service. One developer builds and operates this; the portfolio value lies in
demonstrable judgment, not maximal infrastructure.

## Decision

One FastAPI codebase with strict internal layer boundaries (api / services / repositories / ai /
parsing), deployed as two processes: API server and Celery worker. Module seams are designed so
`workers/` + `ai/` could be extracted into a separate service later.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Microservices per domain | Adds network failure modes, tracing, and deploy complexity that solve a team-scaling problem we don't have |
| Single-process monolith (no worker) | AI jobs (10–60s) would block API workers; no independent scaling of compute-heavy work |

## Consequences

Simpler local dev, one CI pipeline, refactors stay cheap. We commit to enforcing layer
boundaries by convention and review (no import cycles). Revisit if: multiple teams work the
codebase, or worker load requires independent release cadence.
