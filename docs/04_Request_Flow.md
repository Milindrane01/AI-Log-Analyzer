# 04 — Request Flow

## Overview

This document traces the important end-to-end flows through the system. The canonical flow is
**upload → async analysis → poll** (the `202 Accepted` pattern from
[ADR-002](adr/002-celery-for-ai-jobs.md)).

## Flow 1 — Ingestion & analysis (async)

Source: [`diagrams/sequence.mmd`](diagrams/sequence.mmd).

```mermaid
sequenceDiagram
    autonumber
    participant U as Browser
    participant A as FastAPI
    participant P as PostgreSQL
    participant Q as Redis
    participant W as Celery worker
    participant O as OpenAI
    U->>A: POST /api/v1/logs (file|paste) + Bearer
    A->>A: validate, stream to disk, sha256
    A->>P: LogFile + Analysis(PENDING)
    A->>P: COMMIT (before enqueue)
    A->>Q: enqueue analyze(id)
    A-->>U: 202 { analysis_id }
    Q->>W: job
    W->>W: detect → parse → fingerprint → group
    W->>P: ErrorGroups
    opt AI enabled
        W->>O: analyze top-N groups
        W->>P: GroupInsights
    end
    W->>P: Analysis COMPLETED
    loop poll
        U->>A: GET /analyses/{id}
        A-->>U: 200 { status }
    end
    U->>A: GET /analyses/{id}/groups
    A-->>U: 200 { groups + insights }
```

**Critical detail:** the API **commits before enqueue**. Enqueuing inside an uncommitted
transaction lets the worker (separate session) race ahead and find no rows — a real bug caught by
tests. See `backend/app/api/v1/logs.py:_accept`.

## Flow 2 — Authentication

```mermaid
sequenceDiagram
    autonumber
    participant U as Browser
    participant A as FastAPI
    U->>A: POST /auth/register {email,password}
    A-->>U: 201 UserResponse
    U->>A: POST /auth/login {email,password}
    A->>A: verify bcrypt, issue access+refresh
    A-->>U: 200 { access_token, refresh_token }
    U->>A: GET /users/me (Bearer access)
    A-->>U: 200 UserResponse
    Note over U,A: on 401, client POSTs /auth/refresh → new pair, retries once
```

Client-side refresh/retry: `frontend/src/api/client.ts`. Server: `backend/app/services/auth.py`.

## Flow 3 — Chat with logs (SSE streaming)

```mermaid
sequenceDiagram
    autonumber
    participant U as Browser
    participant A as FastAPI
    participant E as Embedder
    participant O as OpenAI
    U->>A: POST /logs/{id}/chat {message} (Bearer)
    A->>P: persist user message (commit before stream)
    A->>A: chunk file → retrieve (E)
    alt retrieval below threshold
        A-->>U: SSE token "I don't see anything about that…" (no LLM call)
    else grounded answer
        A->>O: stream_chat(system, context)
        O-->>A: token stream
        A-->>U: SSE {type:token,...}* then {type:done, citations}
        A->>P: persist assistant message + citations
    end
```

Grounding/refusal logic: `backend/app/ai/pipelines/chat.py`. Endpoint: `backend/app/api/v1/chat.py`.

## Flow 4 — Multi-agent investigation

`POST /analyses/{id}/investigate` → build evidence from timeline → run planner → investigator →
verifier under budget → persist steps → return conclusion + trace. See
[07 AI Architecture](07_AI_Architecture.md) and `backend/app/ai/agents/orchestrator.py`.

## Configuration touchpoints

- Poll interval (frontend): `POLL_MS = 1500` in `frontend/src/pages/Analysis.tsx`.
- Upload caps: `APP_MAX_UPLOAD_BYTES`, `APP_MAX_PASTE_BYTES`.
- AI on/off: `APP_OPENAI_API_KEY` (empty → groups only, chat returns 503).

## Troubleshooting

Analysis stuck in `pending`/`running`? The worker isn't consuming — see
[13 Troubleshooting](13_Troubleshooting.md).

## Interview notes

- **Why 202 + poll, not sync?** LLM calls take 10–60s; holding the request open fails at timeouts,
  retries duplicate cost, threads starve. Follow-up: "how would you push instead of poll?" → SSE
  (already used for chat) or WebSockets; the model doesn't change.
