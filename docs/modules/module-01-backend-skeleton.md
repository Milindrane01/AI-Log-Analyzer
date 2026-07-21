# Module 1 — Backend Skeleton

> What was built, why each piece exists, and what to know for interviews.
> Files: `backend/`, `docker-compose.yml`, `infra/docker/api.Dockerfile`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`

## 1. The Business Problem

Nothing user-visible yet — this module buys **development velocity and safety** for every later
module: identical environments (Docker), machine-enforced quality (CI, pre-commit), and an app
shape that stays testable as it grows (factory + DI). Teams that skip this pay for it with
"works on my machine" bugs and untestable globals.

## 2. File-by-File

### `backend/pyproject.toml` — one manifest for everything
Dependencies, build config, and all tool configs (ruff/black/mypy/pytest) in one file. Why not
requirements.txt: no metadata, no dev/prod split, no tool config — pyproject is the modern
standard (PEP 621). Note `optional-dependencies.dev`: production images install only runtime deps.

### `app/core/config.py` — typed settings (pydantic-settings)
- **12-factor**: config comes from environment variables, never code. Same image runs in
  dev/test/prod with different env.
- **Fail fast**: `APP_ENVIRONMENT=staging-ish` crashes at boot with a clear error instead of
  misbehaving at 3am. Types are validated, not assumed.
- **`@lru_cache` on `get_settings()`**: lazy singleton — env is read once per process. Tests
  clear the cache (see `conftest.py`) so `monkeypatch.setenv` works.
- **Common mistake**: importing a module-level `settings = Settings()` everywhere. That reads
  env at import time, breaks test overrides, and creates hidden coupling. Always go through the
  function → it's also what FastAPI's `Depends` needs.

### `app/core/logging.py` — structured logging (structlog)
- Logs are events with key-value context (`log.info("file_uploaded", size_bytes=n)`), not
  f-strings. JSON in prod (machine-parseable), pretty console in dev.
- Why structlog over stdlib `logging`: bound context (attach `request_id` once, appears on every
  subsequent line), processor pipeline, first-class JSON. Alternatives: `loguru` (nicer stdlib,
  weaker structure), plain `logging` + `python-json-logger` (verbose).
- **Interview**: "Why structured logging?" → because grep is not a query language. JSON logs let
  you ask "all ERRORs for user X in service Y between 10:12–10:15".

### `app/main.py` — application factory + lifespan
- `create_app()` builds the app; nothing happens at import time. Enables per-test apps and kills
  import-order bugs.
- `lifespan` (async context manager): code before `yield` = startup (later: DB pool, redis
  client, ML model load — create once, share across requests); after `yield` = clean shutdown.
  Replaces deprecated `@app.on_event`.
- Docs/OpenAPI URLs are disabled in production — smaller attack surface.

### `app/api/deps.py` — dependency injection wiring
- FastAPI's `Depends` is a DI container: handlers declare *what* they need, this module decides
  *how* it's provided. Tests swap implementations via `app.dependency_overrides` — no
  monkeypatching.
- `SettingsDep = Annotated[Settings, Depends(get_settings)]` — the modern alias pattern; one
  place to change wiring for every handler.

### `app/api/v1/health.py` — two probes, not one
| Probe | Question | K8s reaction on failure |
|---|---|---|
| `/health` (liveness) | Is the process alive? | **Restart** the pod |
| `/health/ready` (readiness) | Can it do real work (deps up)? | **Stop routing traffic**, don't restart |

Classic outage amplifier: putting a DB check in liveness → DB blips → K8s restarts every healthy
API pod simultaneously. This separation is a favorite interview probe.

### `app/schemas/health.py` — response contracts
Every response has a Pydantic schema: documented in OpenAPI, validated on the way out, and the
public contract is decoupled from internal storage (schemas ≠ ORM models).

### `tests/` — in-process ASGI testing
- `httpx.AsyncClient(transport=ASGITransport(app))` calls the app with **no network and no
  server** — sub-millisecond per request.
- `conftest.py` clears the settings cache between tests (cache + monkeypatch = stale-value bugs).
- Note what tests assert: the **contract** (status, fields), not implementation details.

### `infra/docker/api.Dockerfile` — multi-stage build
- Stage 1 (builder) has pip caches and build tools; stage 2 (runtime) ships only the venv + code.
- **Layer-cache trick**: `COPY pyproject.toml` *before* `COPY app` — dependency layer is reused
  unless deps change; code-only rebuilds take seconds.
- Non-root user (`appuser`): container escape ≠ root. `HEALTHCHECK` hits the liveness probe.

### `docker-compose.yml` — one-command dev environment
`docker compose up` = api + postgres16 + redis7, with healthchecks so `depends_on` waits for
*healthy*, not merely *started* (a classic race). `${POSTGRES_PASSWORD:?}` refuses to boot
without a password — no silent insecure defaults. Postgres/redis are wired to the app in M2/M3.

### `.github/workflows/ci.yml` + `.pre-commit-config.yaml` — two quality gates
Pre-commit catches issues in seconds locally; CI is the unbypassable gate on GitHub. Two jobs
(quality / tests) run in parallel and fail independently — you see *what* broke at a glance.

## 3. Tradeoffs Made

| Choice | Alternative | Why this |
|---|---|---|
| structlog | loguru, stdlib | structured-first, bound context, JSON native |
| pip + pyproject | poetry, uv | zero extra tooling to learn now; uv is a drop-in speedup later |
| ruff **and** black | ruff-format alone | brief specified both; they don't conflict (E501 ignored, same line length) |
| healthcheck via urllib | curl in image | no extra binary in the runtime image |

## 4. Verification Performed

- `pytest`: 7/7 passing (health contract, readiness, 404, config defaults/override/validation/caching)
- App factory imports and serves routes in-process
- ruff/black/mypy run in CI (sandbox couldn't download ruff's binary; CI is the enforcement point)

## 5. Improvement Backlog (deliberate deferrals)

- Request-ID middleware + access-log enrichment (M2, with auth)
- Central exception handlers → RFC-7807 problem responses (M2)
- Readiness checks for postgres/redis/qdrant (M2/M3)
- `uv` for faster installs; Dependabot/Renovate for dep updates
- Coverage threshold gate in CI (add once there's meaningful logic to cover)

## 6. Interview Questions From This Module

1. Liveness vs readiness — and what goes wrong if you conflate them?
2. Why an app factory instead of a module-level `FastAPI()`?
3. How does FastAPI's DI improve testability over imports/globals? (`dependency_overrides`)
4. Why multi-stage Docker builds? What determines layer-cache hits?
5. Why must config validation fail at startup rather than first use?
6. What makes a log line "structured", and why does it matter at scale?
