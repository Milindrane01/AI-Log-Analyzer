# 14 — Developer Guide

## Overview

How to set up, run, test, and extend the codebase. Complements
[`docs/guides/developer-guide.md`](guides/developer-guide.md) with handover-level detail.

## Prerequisites

Python 3.12+, Node 20+, Docker Desktop (for the full stack).

## Setup

```bash
bash scripts/setup.sh        # macOS/Linux: venv + deps + node_modules + runs tests
# Windows: powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
```

Or full stack: `cp backend/.env.example backend/.env && docker compose up --build`.

## Run locally (dev loop)

```bash
# infra only
docker compose up postgres redis qdrant
# backend (venv active)
cd backend && uvicorn app.main:app --reload
# frontend
cd frontend && npm run dev        # Vite proxies /api → :8000
```

## Test & quality gates

```bash
cd backend && pytest              # 99 tests offline
ruff check . && black --check . && mypy app
cd ../frontend && npm run typecheck && npm run build
```

See [11 Testing](11_Testing.md).

## Project map

See [03 Low-Level Design](03_Low_Level_Design.md) for the full package layout and layer rules.

## How to extend — common recipes

### Add a new log format parser
1. Create `backend/app/parsing/parsers/<name>.py` implementing `sniff()` + `parse_line()`.
2. Register it in `parsing/parsers/__init__.py:REGISTRY` (before `PlainParser`, which must stay last).
3. Add fixtures/tests in `tests/unit/test_parsing.py`.

### Add a new API endpoint
1. Add a router in `backend/app/api/v1/<area>.py`; use `CurrentUser`, `DBDep`, `SettingsDep`.
2. Put business logic in `services/`; data access in `repositories/` or a service query.
3. Define Pydantic schemas in `schemas/`.
4. Register the router in `api/v1/router.py`.
5. Add tests; update [05 API Documentation](05_API_Documentation.md).

### Add a new AI capability
1. Prefer an interface + fake (follow `LLMProvider`/`EmbeddingProvider` pattern).
2. Keep prompts in `ai/prompts/` (versioned); guard untrusted input via `ai/guards`.
3. Validate model output against a Pydantic schema.

### Add a migration
`cd backend && alembic revision -m "..."`, edit the file, `alembic upgrade head`. See
[06 Database Design](06_Database_Design.md).

## Coding conventions

Conventional commits; feature branch → PR → CI green → squash (`CONTRIBUTING.md`). Update the
relevant module doc, `progress.md`, `CHANGELOG.md`, and `.env.example` in the same PR
(`.github/PULL_REQUEST_TEMPLATE.md` enforces the checklist).

## Frontend notes

React + TS + Tailwind; typed client with in-memory access token + localStorage refresh + 401→retry
(`frontend/src/api/client.ts`); SSE via fetch+ReadableStream. Same-origin (no CORS).

## Best practices / common pitfalls

- **Do** go through interfaces so tests stay offline.
- **Pitfall:** calling `session.commit()` in a request-path service (the `get_db` dependency owns it).

## Interview notes

- **Onboarding story:** "clone, `bash scripts/setup.sh`, `pytest` green in 30s — no keys or infra."
  That reproducibility is the point.
