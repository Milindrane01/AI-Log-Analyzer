# Module 6 — Frontend v1 (React + TypeScript + Tailwind)

> **Status:** ✅ Built (2026-07-18) · tsc strict + production vite build verified
> Depends on: Modules 2–5 (stable API contract)

## As built — deviations from plan & key notes

- **Hand-written typed client** (`src/api/types.ts` mirrors the Pydantic schemas) instead of
  OpenAPI codegen — at 15 endpoints the generator toolchain costs more than it saves; revisit
  if the API triples. The client auto-refreshes on 401 (one retry) and rotates the pair.
- **Token strategy (documented tradeoff):** access token in memory only (XSS can't read what
  isn't stored); refresh token in localStorage. The stricter alternative — httpOnly cookies —
  needs CSRF machinery; deliberate scope call for a portfolio SPA.
- **Zero CORS anywhere, by architecture:** vite dev proxies `/api` → localhost:8000; in
  production nginx serves the SPA and reverse-proxies `/api` → api:8000. One origin, no
  preflight headaches — this is the pattern to remember.
- **Polling per ADR-002:** the analysis page polls every 1.5s until COMPLETED/FAILED; SSE is
  the M7 upgrade. Groups without insights render sample lines (AI-disabled degradation is a UI
  state, exactly as designed in M4).
- **No TanStack Query / state library** — at four pages, React state + effects is the honest
  size. Component tests (Vitest) deferred to ride along with M7's chat UI work.

## Goal

The product becomes usable by someone who isn't reading Swagger. Built now — not earlier —
because the API contract stabilized through M4/M5; UI built against a moving API is double work.

## What gets built

- [x] Vite + React + TypeScript (strict) + Tailwind scaffold in `frontend/`
- [x] Typed API client with 401→refresh→retry flow (hand-written; codegen deferred)
- [x] Auth: login/register tabs, session restore on refresh, RequireAuth route guard
- [x] Upload view: drag-drop + browse + paste box, 202→poll handoff
- [x] Results dashboard matching the session mockup: severity-badged group rail,
      root cause / explanation / reasons / fix / commands / confidence panel
- [x] History table with pagination + similar-incident links on the analysis page
- [x] Error/loading/empty states; dark theme
- [x] nginx frontend service in compose (SPA fallback + /api reverse proxy, 60m body cap)
- [ ] Component tests (Vitest) — deferred to M7 alongside chat UI

## Key concepts you'll learn

OpenAPI-generated clients (why hand-written fetch wrappers rot); token handling in SPAs
(memory vs localStorage tradeoffs, refresh flows); polling vs SSE from the client side;
component state vs server state (TanStack Query); Tailwind composition patterns.

## Planned files

`frontend/src/api/` (generated client), `frontend/src/pages/{Login,Upload,Analysis,History}.tsx`,
`frontend/src/components/`, `infra/docker/frontend.Dockerfile`

## Acceptance criteria (demo)

Full flow in a browser: register → upload the sample log → watch status → browse grouped
errors → open the DB-timeout analysis and see the mockup made real.
