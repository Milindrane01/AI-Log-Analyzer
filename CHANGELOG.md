# Changelog

All notable changes to this project. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning: [SemVer](https://semver.org/) once the API is public (0.x until then).

## [Unreleased]

### Added
- MIT `LICENSE`
- CI frontend job (typecheck + build) and a 70% backend coverage floor
- Readiness probe now pings the vector store when similarity search is configured
- `docs/planning/05-backlog.md` — consolidated pending/refinement backlog

- Enterprise handover documentation set: `docs/README.md` + 18 numbered docs (01–18) covering
  overview, architecture, LLD, request flow, API, database, AI, DevOps, security, performance,
  testing, operations, troubleshooting, developer/user guides, interview guide, KT, and FAQ
- Six Mermaid diagram sources in `docs/diagrams/` (architecture, sequence, erd, ai_pipeline,
  deployment, ci_cd), embedded inline across the docs
- Recruiter-grade README: badges, highlights, inline Mermaid architecture diagram, screenshot slot
- `docs/portfolio/related-work.md` mapping the project to published RCA/LLM-log research
- `.gitattributes` so GitHub language stats reflect real source

### Changed
- Removed the unrelated evlog experiment leftovers (`.claude/skills`, `skills-lock.json`)

### Security
- `.gitignore` the filled `infra/k8s/secret.yaml` (only the `.example` is committed)

## [1.0.0] — 2026-07-20 · Milestone 10: production hardening · FEATURE-COMPLETE

### Added
- Prometheus RED metrics (`/metrics`) via dependency-free middleware; route-templated to avoid
  high-cardinality series
- Kubernetes manifests: namespace, ConfigMap, Secret (example), data stores, api/worker/frontend
  Deployments + Services, Ingress, HPA (api + worker)
- Monitoring stack: Prometheus scrape config, alert rules, Grafana dashboard; both in compose
- Locust load test (`tests/performance/locustfile.py`) modeling the real hot path
- Guides: deployment, developer, user; portfolio docs: resume bullets, interview Q&A, system design
- 3 metrics tests

### Milestone
- **All 11 milestones complete; all 10 AI phases delivered; 99 backend tests green.**

## [0.9.0] — 2026-07-20 · Milestone 9: timeline & multi-agent investigation (phases 9–10)

### Added
- Deterministic incident timeline: groups ordered by first occurrence, first-failure marked;
  `GET /analyses/{id}/timeline`
- Multi-agent investigation: planner → investigator → verifier over a read-only evidence toolbox
- Orchestrator with hard budgets (max steps + wall-clock deadline), graceful over-budget exit
- Verifier refuses causation without a genuine trigger + cascade (correlation-not-causation guard)
- Investigation + step-trace models (migration 006); full trace persisted and API-exposed
- Endpoints: `POST /analyses/{id}/investigate`, `GET /analyses/{id}/investigation`
- Frontend: visual timeline (first-failure highlighted) + investigation panel with agent trace
- 10 new tests (agent roles/budgets/verification + cascade timeline + isolation)

### Milestone
- **All 10 AI phases from the project brief are now delivered.**

## [0.8.0] — 2026-07-18 · Milestone 8: remediation & incident reports (phases 6–8)

### Added
- Command catalog: 13 read-only diagnostic templates (kubernetes/linux/aws) with regex-validated
  params; `render_command` allow-lists structure so injection is impossible by construction
- Deterministic command selector: error_type → template ids → validated rendered commands
- IncidentReport model (migration 005) + deterministic markdown generator
  (summary/impact/findings/prevention), idempotent per analysis
- Endpoints: POST/GET `/analyses/{id}/report`, `GET .../report.md` download,
  `GET .../groups/{id}/commands`
- Frontend: incident-report button, report panel, markdown download link
- 13 new tests incl. catalog-wide read-only guard and param-injection rejection

## [0.7.0] — 2026-07-18 · Milestone 7: chat with logs (phase 5)

### Added
- Log-aware RAG: overlapping line-window chunking with provenance; huge-file stride widening
- Hybrid retrieval: stopword-filtered query-term coverage (prefix matching) + cosine tiebreak
- Grounded chat pipeline: deterministic refusal below retrieval threshold (zero LLM calls),
  citation line-ranges recorded per answer
- `stream_chat` on providers: OpenAI SSE passthrough + deterministic mock streaming
- Conversations/messages (migration 004), one per (user, log file); user turn committed pre-stream
- `POST /logs/{id}/chat` (SSE) + `GET /logs/{id}/chat` history; 503 when AI unconfigured
- Chat UI: streaming bubbles, evidence footers, history restore; dashboard entry button
- 10 new tests (chunking coverage/cap, retrieval hit/miss, SSE grounding, persistence,
  refusal-without-call, isolation)

## [0.6.0] — 2026-07-18 · Milestone 6: frontend v1

### Added
- React 18 + TypeScript (strict) + Tailwind SPA in `frontend/`
- Typed API client: in-memory access token, localStorage refresh token, 401→refresh→retry
- Auth pages with session restore; route guard
- Upload page (drag-drop + paste), analysis dashboard (group rail, insight panel, commands,
  confidence, cached badge, similar incidents), paginated history
- nginx image: SPA fallback + same-origin `/api` reverse proxy (no CORS anywhere)
- `frontend` service in docker-compose on port 3000

## [0.5.0] — 2026-07-18 · Milestone 5: memory & similar-incident search (phase 4)

### Added
- `EmbeddingProvider` seam: HashingEmbedder (deterministic, dep-free) + SentenceTransformerEmbedder (lazy torch)
- `VectorStore` seam: InMemoryVectorStore (tests) + QdrantVectorStore (REST, server-side user filter)
- Pipeline indexes error-group templates on analysis completion (failure-tolerant)
- `GET /analyses/{id}/similar` — cross-analysis matches with cosine scores, threshold 0.4
- `GET /analyses` — paginated history with filenames, newest first
- qdrant service in docker-compose (persistent volume, healthcheck)
- 8 new tests: embedding math, store isolation/ordering, cross-analysis and cross-user flows

## [0.4.0] — 2026-07-18 · Milestone 4: first AI analysis (phases 1–3)

### Added
- `LLMProvider` seam: OpenAI (raw httpx, strict json_schema structured output) + deterministic mock
- Prompt `analysis-v1`: SRE persona, few-shot example, confidence guidance, injection rule
- Injection guards: data fencing with scrubbed delimiters, length caps, deny-by-default
  read-only command allow-list (chaining/mutation/destructive all rejected)
- `group_insights` table (migration 003): validated payload, model, prompt version, token usage
- Fingerprint-keyed insight cache: identical error groups never hit the LLM twice per user
- AI severity refinement over the M3 level heuristic
- Graceful degradation: provider failure → analysis completes with groups, no insights
- Insights embedded in `GET /analyses/{id}/groups` responses
- 12 new tests incl. the brief's example input → expected output contract

### Config
- `APP_OPENAI_API_KEY` (empty = AI disabled), model tiering, `APP_AI_MAX_GROUPS_PER_ANALYSIS`

## [0.3.0] — 2026-07-18 · Milestone 3: log ingestion & parsing

### Added
- Models + migration: LogFile, Analysis (status machine), ErrorGroup with samples
- Parser registry: JSON lines, logfmt, syslog, freeform fallback; head-sample format detector
- Error fingerprinting: uuid/timestamp/ip/hex/quote/path/number normalization → sha256 groups
- Analysis pipeline: stream file → parse → group WARNING+ → persist, FAILED on any error
- Celery worker (acks_late, prefetch=1) + TaskQueue abstraction (inline queue for tests)
- Endpoints: POST /logs (multipart, streamed, 50MB cap), POST /logs/paste (1MB cap),
  GET /analyses/{id}, GET /analyses/{id}/groups (paginated, count-ordered)
- docker-compose: worker service + shared uploads volume; redis wired to api/worker
- 22 new tests (parsers, detector, fingerprint stability, end-to-end ingestion, isolation)

### Fixed
- Commit-before-enqueue ordering: enqueueing inside an uncommitted transaction let the
  worker race ahead of the data (caught by integration tests)

## [0.2.0] — 2026-07-18 · Milestone 2: auth & users

### Added
- Async SQLAlchemy engine with session-per-request dependency (commit/rollback centralized)
- User + AuditLog models, Alembic async migration setup with initial revision
- bcrypt password hashing; JWT access/refresh pair with type-checked claims and rotation
- Endpoints: register, login, refresh, users/me (Bearer auth)
- Sliding-window rate limiting on auth routes (in-memory; Redis planned M3)
- Central domain-exception handlers → consistent JSON errors; generic 500s
- Readiness probe now pings the database
- Production boot refuses the development JWT secret
- Tests: 22 total (security unit + full auth-flow integration on SQLite)

### Changed
- structlog: removed stdlib-only `add_logger_name` processor (broke under PrintLogger)

## [0.1.1] — 2026-07-17

### Added
- Project management layer: ADRs (001–003), risk register, PR/issue templates, this changelog

## [0.1.0] — 2026-07-17 · Milestone 1: backend skeleton

### Added
- FastAPI app factory with lifespan management, versioned `/api/v1` router
- Typed configuration via pydantic-settings (fail-fast validation, cached accessor)
- Structured logging (structlog): JSON in prod, pretty console in dev
- Liveness (`/health`) and readiness (`/health/ready`) probes with Pydantic schemas
- Test suite: in-process ASGI tests, 7 tests (health contract, config behavior)
- Multi-stage Dockerfile (non-root, healthcheck), docker-compose with postgres 16 + redis 7
- GitHub Actions CI (ruff, black, mypy, pytest) and pre-commit hooks

## [0.0.1] — 2026-07-16 · Milestone 0: planning

### Added
- Requirements & scope, architecture (Mermaid + tradeoffs), roadmap (M0–M10), git strategy
- Module explainer docs 01–10 and progress tracker
