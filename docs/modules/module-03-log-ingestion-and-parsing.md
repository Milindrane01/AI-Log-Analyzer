# Module 3 — Log Ingestion & Parsing

> **Status:** ✅ Built (2026-07-18) · 44/44 total tests passing
> Depends on: Module 2

## As built — deviations from plan & key notes

- **No LogEntry table.** Persisting 1M rows per 50MB file bloats postgres for little value.
  Groups carry up to 5 raw sample lines (JSON); the raw file stays on disk for M7's RAG.
- **TaskQueue abstraction over raw Celery**: API depends on a `TaskQueue` protocol —
  `CeleryTaskQueue` in production, `InlineTaskQueue` in tests (runs the real pipeline
  in-process, zero infra). Celery worker ships in compose (`worker` service, shared uploads volume).
- **Commit-before-enqueue** — the integration tests caught a live race: enqueueing inside an
  uncommitted transaction lets the worker race ahead and find no rows. The fix (explicit commit
  before `.delay()`) is *the* classic async-job lesson; transactional outbox is the M10-grade answer.
- **Property-based tests via parametrization** rather than hypothesis (one less dependency);
  determinism test hashes the same input 50×.
- **Severity in M3 is a level heuristic** (critical→critical, error→high, warning→medium).
  M4's AI refines it with content understanding.
- Deferred from plan to M4+: Redis-backed rate limiter + refresh-token denylist (need the
  redis client wired into app state), per-user storage quota beyond per-file caps.

## Goal

The deterministic heart of the product. Raw logs become structured, deduplicated error groups
*before* any AI sees them — this is the main cost lever (212 duplicate timeouts = 1 analysis)
and the main quality lever (the LLM gets clean, grouped evidence instead of 50MB of noise).

## What gets built

- [x] `POST /logs` file upload (streaming to disk, size validation) + `POST /logs/paste`
- [x] `LogFile`, `ErrorGroup`, `Analysis` models + migration 002 (LogEntry dropped — see above)
- [x] Format detection: JSON lines, syslog, logfmt, freeform fallback
- [x] Parser registry (`LogParser` protocol) — each format is a pluggable parser
- [x] Error fingerprinting: normalize uuids/timestamps/ips/hex/quotes/paths/numbers → sha256
- [x] Celery worker + task pipeline: parse → group → persist (PENDING→RUNNING→COMPLETED/FAILED)
- [x] `GET /analyses/{id}` status polling + paginated `GET /analyses/{id}/groups`
- [x] Per-file caps (50MB upload / 1MB paste) with 413 responses
- [x] Test fixtures per format (JSON lines incl. NDJSON-shape, syslog, logfmt, plain)
- [x] Fingerprint stability tests (parametrized; hypothesis deferred)

## Key concepts you'll learn

Streaming uploads without loading files in memory; content-based fingerprinting (how Sentry
groups errors); Celery task design (idempotency, retries, acks-late); state machines for job
status; why parsers are a registry not an if/else ladder (open-closed principle).

## Planned files

`app/parsing/detector.py`, `app/parsing/parsers/*.py`, `app/parsing/fingerprint.py`,
`app/models/log.py`, `app/repositories/log.py`, `app/services/ingestion.py`,
`app/workers/celery_app.py`, `app/workers/tasks.py`, `app/api/v1/logs.py`, `app/api/v1/analyses.py`

## Acceptance criteria (demo)

Upload a 50MB mixed log file → 202 with analysis id → poll until COMPLETED → grouped error list
with counts and severities, correctly deduplicated. No AI involved yet.
