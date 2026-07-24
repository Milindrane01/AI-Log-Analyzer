# 05 — API Documentation

## Overview

REST API under prefix `/api/v1`, served by FastAPI. **Interactive, always-current docs** are
auto-generated at `/docs` (Swagger UI) and `/redoc` — disabled in production for attack-surface
reduction (`backend/app/main.py`). This document is the human-readable contract; the OpenAPI schema
at `/openapi.json` is the machine source of truth.

## Conventions

- **Auth:** `Authorization: Bearer <access_token>` on all endpoints except register/login/refresh
  and health.
- **Errors:** consistent body `{"error": {"code": "...", "message": "..."}}` (see
  [09 Security](09_Security.md) / `backend/app/core/exceptions.py`).
- **Ownership:** accessing another user's resource returns **404** (not 403) — no existence leak.
- **Async analysis:** ingestion returns `202 Accepted`; clients poll (see [04](04_Request_Flow.md)).

## Endpoint reference

Verified against `backend/app/api/v1/*.py`.

### Health

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/health` | no | Liveness (process up) |
| GET | `/api/v1/health/ready` | no | Readiness (DB + vector store reachable) |
| GET | `/metrics` | no | Prometheus exposition (not under `/api/v1`) |

### Auth & users

| Method | Path | Auth | Body / notes |
|---|---|---|---|
| POST | `/api/v1/auth/register` | no | `{email, password(≥10)}` → 201 UserResponse; rate-limited 5/60s |
| POST | `/api/v1/auth/login` | no | `{email, password}` → `{access_token, refresh_token}`; 10/60s |
| POST | `/api/v1/auth/refresh` | no | `{refresh_token}` → new pair (rotation) |
| GET | `/api/v1/users/me` | yes | Current user |

### Logs (ingestion)

| Method | Path | Auth | Body / notes |
|---|---|---|---|
| POST | `/api/v1/logs` | yes | multipart `file`; ≤50MB; → 202 `{analysis_id, log_file_id, status}`; 10/60s |
| POST | `/api/v1/logs/paste` | yes | `{content, filename?}`; ≤1MB; → 202; 20/60s |

### Analyses

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/analyses` | yes | Paginated history (newest first); `?limit&offset` |
| GET | `/api/v1/analyses/{id}` | yes | Analysis status + stats |
| GET | `/api/v1/analyses/{id}/groups` | yes | Error groups (count-ordered) + insights; `?limit&offset` |
| GET | `/api/v1/analyses/{id}/similar` | yes | Similar past incidents (or `{enabled:false}`) |
| GET | `/api/v1/analyses/{id}/timeline` | yes | Causal event timeline, first-failure marked |
| POST | `/api/v1/analyses/{id}/investigate` | yes | Run multi-agent investigation; 5/60s |
| GET | `/api/v1/analyses/{id}/investigation` | yes | Latest investigation + step trace |

### Reports & commands

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/analyses/{id}/report` | yes | Generate/regenerate incident report (idempotent); 10/60s |
| GET | `/api/v1/analyses/{id}/report` | yes | Get report (JSON) |
| GET | `/api/v1/analyses/{id}/report.md` | yes | Download report as markdown |
| GET | `/api/v1/analyses/{id}/groups/{group_id}/commands` | yes | Safe remediation commands for a group |

### Chat

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/logs/{log_file_id}/chat` | yes | Conversation history |
| POST | `/api/v1/logs/{log_file_id}/chat` | yes | Ask a question → **SSE stream**; 20/60s; 503 if AI unconfigured |

## SSE event format (chat)

```
data: {"type":"token","text":"..."}      # repeated
data: {"type":"done","message_id":"...","citations":[{"start_line":1,"end_line":40}]}
data: {"type":"error","message":"..."}    # on failure
```

Consumed with `fetch` + `ReadableStream` (not `EventSource`, which can't send auth headers) —
`frontend/src/api/client.ts:chatStream`.

## Example

```bash
# register, login, capture token
curl -sX POST localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"a-long-passphrase"}'
TOKEN=$(curl -sX POST localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","password":"a-long-passphrase"}' | jq -r .access_token)
# paste a log → get analysis id
curl -sX POST localhost:8000/api/v1/logs/paste -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"content":"2026-07-15 10:12:14 ERROR Database connection timeout"}'
```

## Security / performance / scaling

Auth & rate limits per endpoint above; see [09](09_Security.md) and [10](10_Performance_and_Scaling.md).

## Interview notes

- **Why 404 for another user's resource?** Returning 403 confirms the ID exists (enumeration leak).
- **Why is analysis async?** See [ADR-002](adr/002-celery-for-ai-jobs.md).
