# System Design Explanation

## End-to-end request flow

```
Browser (React SPA)
  │  POST /api/v1/logs  (upload/paste)
  ▼
FastAPI api  ── validate, stream to disk, create Analysis(PENDING) ──► PostgreSQL
  │  202 Accepted {analysis_id}                         enqueue │
  │                                                             ▼
  │                                                          Redis (broker)
  │                                                             │ consume
  ▼  GET /analyses/{id}  (poll)                                 ▼
FastAPI ◄──────────────────────────────────────────  Celery worker
                                                        detect → parse → fingerprint/group
                                                        → LLM insights (OpenAI)
                                                        → embed + index (Qdrant)
                                                        → status COMPLETED
```

Non-AI endpoints stay fast (p95 target < 300ms) because all heavy work is off-request. The worker
is the same image as the api, different command — one codebase, independent scaling.

## Data model (6 migrations)

`users` → `log_files` → `analyses` → `error_groups` → `group_insights`
plus `audit_logs`, `conversations`/`messages`, `incident_reports`,
`investigations`/`investigation_steps`. Everything user-owned; UUID PKs (no enumeration, safe to
expose).

## The interface pattern (why everything is testable)

| Interface | Prod impl | Test/dev impl |
|---|---|---|
| `LLMProvider` | OpenAI (httpx, structured output + SSE) | `MockLLMProvider` (deterministic) |
| `TaskQueue` | Celery + Redis | `InlineTaskQueue` (runs pipeline in-process) |
| `EmbeddingProvider` | sentence-transformers (lazy torch) | `HashingEmbedder` (bag-of-words) |
| `VectorStore` | Qdrant (REST) | `InMemoryVectorStore` |
| Database | PostgreSQL | SQLite (aiosqlite) |

This is the single most important structural decision: it makes a 99-test suite run offline in
seconds, and it means swapping any vendor is a one-file change.

## Scaling levers

- **Cost**: group-before-LLM dedup, fingerprint insight cache, model tiering, top-N cap.
- **Throughput**: stateless api (HPA on CPU), horizontally scaled workers (queue-depth autoscaling
  in production), Redis-backed rate limiting.
- **Latency**: async everywhere, connection pooling, `202`+poll for slow work, SSE for chat.
- **Data**: route-templated metrics, payload-filtered vector search, pagination on all list APIs.

## Deliberate boundaries

- Suggest commands, never execute — a safety boundary, and read-only templates only.
- AI is an enhancement layer: every feature degrades gracefully to a working non-AI state.
- Deterministic core (parsing, grouping, timeline, command rendering) so the reproducible parts
  never depend on a model.
