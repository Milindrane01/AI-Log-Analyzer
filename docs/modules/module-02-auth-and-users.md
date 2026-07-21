# Module 2 — Auth & Users

> **Status:** ✅ Built (2026-07-18) · 22/22 tests passing
> Depends on: Module 1

## As built — deviations from plan & key notes

- **bcrypt directly, not passlib** — passlib is unmaintained and breaks with bcrypt≥4.1.
- **Rate limiting is in-memory per-process** (`core/ratelimit.py`), not Redis: correct interface,
  simplest storage. Swaps to Redis in M3 when the client lands. Known limit for multi-worker deploys.
- **HTTPBearer (JSON login), not OAuth2 password form** — avoids the python-multipart dependency;
  Swagger's Authorize button still works with the bearer token.
- **Refresh rotation without server-side denylist** — jti claim is present; Redis denylist lands
  in M3 to make rotation airtight against replay.
- **Tests run on SQLite (aiosqlite)** — repositories only speak SQLAlchemy, so the swap is one URL.
- Security details worth remembering: same 401 message for unknown email vs wrong password
  (no user enumeration); generic 500s (no stack traces to clients); commit/rollback lives ONLY
  in the `get_db` dependency (request = one transaction); production boot refuses the dev JWT secret.

## Goal

Every later table hangs off a `user_id`, and every endpoint needs an identity to authorize,
rate-limit, and audit. Retrofitting auth is the most painful refactor in backend work — so it
lands before any product feature.

## What gets built

- [x] SQLAlchemy 2.0 async engine + session management (lifespan-managed pool)
- [x] `User` ORM model + Alembic migrations (init + first revision)
- [x] Repository pattern: `UserRepository` (the template every later repo follows)
- [x] Password hashing (bcrypt) — never store plaintext, ever
- [x] JWT: short-lived access token + refresh token rotation
- [x] Endpoints: `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `GET /users/me`
- [x] `get_current_user` dependency → protected routes
- [x] Rate limiting on auth endpoints (in-memory M2 → Redis in M3)
- [x] Central exception handlers → consistent JSON error responses
- [x] `AuditLog` model + audit events for register/login/refresh failures
- [x] Readiness check: postgres ping
- [x] Tests: unit (hashing, token expiry/tamper) + integration (register→login→me flow)

## Key concepts you'll learn

Async SQLAlchemy session-per-request pattern; why refresh tokens rotate (stolen-token
detection); JWT claims and expiry tradeoffs (stateless vs revocable); repository pattern as the
seam that makes services testable; Alembic autogenerate and its limits; timing-safe comparisons.

## Planned files

`app/models/user.py`, `app/models/audit.py`, `app/repositories/user.py`,
`app/services/auth.py`, `app/core/security.py`, `app/api/v1/auth.py`, `app/api/v1/users.py`,
`app/core/db.py`, `alembic/`, `tests/unit/test_security.py`, `tests/integration/test_auth_flow.py`

## Acceptance criteria (demo)

Register a user, log in, call `GET /users/me` with the token, refresh the token, see a 401 with
a tampered token, see a 429 after hammering login — all via Swagger UI, all tests green in CI.
