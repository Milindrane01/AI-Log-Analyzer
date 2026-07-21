# Roadmap & Milestones — AI Log Analyzer

> Each milestone ships something demonstrable and merges to `main` green.
> AI Phases 1–10 from the project brief are mapped onto milestones below.

## Milestone Map

| # | Milestone | Contains | AI Phases | Demo at the end |
|---|---|---|---|---|
| M0 | **Planning & repo** | Requirements, architecture, roadmap, git strategy, repo init | — | This document set |
| M1 | **Backend skeleton** | FastAPI app factory, config (pydantic-settings), structured logging, health endpoints, Docker + docker-compose (api, postgres, redis), CI (ruff/black/mypy/pytest), pre-commit | — | `docker compose up` → `/health` green, CI badge |
| M2 | **Auth & users** | User model, Alembic migrations, register/login, JWT access+refresh, protected routes, rate limiting, audit log | — | Register → login → call protected route |
| M3 | **Log ingestion & parsing** | Upload + paste endpoints, validation, format detection, parsers (JSON/syslog/logfmt/freeform), error fingerprinting & grouping, Celery pipeline, analysis status polling | — | Upload 50MB file → grouped error list, no AI yet |
| M4 | **First AI analysis** | LLMProvider interface + OpenAI impl, structured outputs, prompt-injection guards, confidence scores, cost controls, mocked-AI test suite | 1, 2, 3 | The brief's example: paste DB timeout log → classified, root-caused, explained |
| M5 | **Memory & search** | Embeddings (sentence-transformers), Qdrant, similar-incident search, analysis history UX | 4 | "Have we seen this before?" returns past incidents |
| M6 | **Frontend v1** | React+TS+Tailwind: auth, upload, results view, history | — | End-to-end in the browser |
| M7 | **Chat with logs (RAG)** | Chunking, retrieval, conversation persistence, streaming responses | 5 | Ask questions about an uploaded log |
| M8 | **Remediation & reports** | Command suggestion (allow-listed templates for shell/K8s/AWS), incident report generator | 6, 7, 8 | Generate a postmortem-ready report |
| M9 | **Timeline & multi-agent** | Incident timeline reconstruction, multi-agent investigation (planner/investigator/verifier) | 9, 10 | Complex multi-service log → investigation narrative |
| M10 | **Production hardening** | K8s manifests (Deployment/Service/Ingress/HPA/Secrets), Prometheus + Grafana, perf tests, deployment guide, resume bullets | — | Deployed on a cluster, dashboards live |

## Sequencing Rationale

- **Auth before ingestion (M2 < M3):** every later table has a `user_id` foreign key; retrofitting auth is painful.
- **Parsing before AI (M3 < M4):** the AI analyzes *grouped, structured* errors, not raw text — this is the main cost/quality lever. Getting deterministic parsing right first also gives us fixtures to test AI against.
- **Docker + CI in M1, not at the end:** infrastructure added late always breaks; added early it's free discipline.
- **Frontend at M6, not M1:** the API contract stabilizes through M4–M5; building UI against a moving API doubles rework. (Swagger UI is our interim frontend.)
- **Multi-agent last:** it composes every prior capability; building it early would mean rebuilding it.

## Definition of Done (every milestone)

1. Code reviewed via PR (feature branch → main, conventional commits)
2. Unit + integration tests pass in CI; no mypy/ruff errors
3. OpenAPI docs updated automatically (FastAPI) + README section updated
4. Demo script in `docs/demos/` runs end-to-end
5. No secrets in code; new env vars documented in `.env.example`
