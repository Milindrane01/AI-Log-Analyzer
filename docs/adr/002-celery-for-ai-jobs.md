# ADR-002: Run AI analysis as Celery jobs behind 202 Accepted

- **Status:** Accepted
- **Date:** 2026-07-16
- **Deciders:** TG

## Context

LLM analysis of a log file takes 10–60+ seconds. HTTP requests held open that long hit client
timeouts, proxy limits, and duplicate-retry cost; API worker threads starve under load.

## Decision

Uploads return `202 Accepted` with an analysis id immediately. Parsing and AI analysis run as
Celery tasks (Redis broker); clients poll `GET /analyses/{id}` (SSE push later). Tasks are
idempotent and retried with backoff.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Synchronous request/response | Timeouts, thread starvation, retries double LLM spend |
| FastAPI BackgroundTasks | Dies with the process; no retries, visibility, or horizontal scaling |
| arq / RQ / Dramatiq | Viable and lighter, but Celery's monitoring (Flower), retry semantics, and industry adoption fit the portfolio goal |

## Consequences

Extra moving part (worker + broker) in every environment — accepted as core to the product.
Job status becomes first-class domain state (PENDING/RUNNING/COMPLETED/FAILED/DEGRADED).
Revisit if: task volume is trivial forever (unlikely) or we move to serverless execution.
