# Developer Guide

## Setup

```bash
# Windows: powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
bash scripts/setup.sh          # venv + deps + node_modules + runs tests
```

Or manually: `cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]"`.

## Run the test suite

```bash
cd backend && pytest              # 99 tests, SQLite-backed, no infra needed
pytest --cov=app                  # with coverage
ruff check . && black --check . && mypy app
```

Frontend: `cd frontend && npm run typecheck && npm run build`.

## Architecture at a glance

Clean-architecture layers, dependencies pointing inward:

```
api/ (routers, deps)  →  services/ (use-cases)  →  repositories/ (data)  →  models/
                              ↓
                          ai/ (providers, prompts, guards, rag, agents, commands)
                          parsing/ (detector, parsers, fingerprint)
```

The recurring pattern that makes it all testable: **every external dependency sits behind an
interface with a fake for tests** — `LLMProvider` (mock), `TaskQueue` (inline), `EmbeddingProvider`
(hashing), `VectorStore` (in-memory). The full suite runs offline with zero API calls or infra.

## Where things live

| Concern | Location |
|---|---|
| Config / secrets | `app/core/config.py` (pydantic-settings) |
| DB session, migrations | `app/core/db.py`, `alembic/` |
| Auth (JWT, bcrypt) | `app/core/security.py`, `app/services/auth.py` |
| Log parsing + grouping | `app/parsing/` |
| AI analysis | `app/ai/`, `app/services/pipeline.py` |
| Background jobs | `app/workers/`, `app/core/queue.py` |
| Metrics | `app/core/metrics.py` → `/metrics` |

## Adding a migration

```bash
cd backend && alembic revision -m "add X"     # then edit the generated file
alembic upgrade head
```

## Conventions

Conventional commits, feature branch → PR → CI green → squash (see `CONTRIBUTING.md`). Update the
module doc, `progress.md`, and `CHANGELOG.md` in the same PR as the change (`.github/PULL_REQUEST_TEMPLATE.md`
enforces this checklist).
