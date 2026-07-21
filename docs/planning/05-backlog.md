# Backlog — pending items & refinements

> The project is feature-complete (all 11 milestones, all 10 AI phases, 99 tests). Nothing here
> is required for the brief; this is the honest "what's next / what was deliberately deferred" list,
> ranked so it's clear what actually moves the needle.

## Tier 1 — quick wins (low effort, real value) — ✅ done in this pass

- [x] `LICENSE` (MIT) — recruiter-friendly, unblocks public repo
- [x] `.gitignore` the filled K8s `secret.yaml` (only `secret.example.yaml` is committed)
- [x] CI: add a **frontend job** (typecheck + build) — CI previously only gated the backend
- [x] CI: fail under a **coverage floor** on core logic
- [x] Readiness probe pings the **vector store** when configured (closes the M3 readiness deferral)

## Tier 2 — engineering hardening (medium effort)

- [ ] **Redis-backed rate limiter + refresh-token denylist (jti)** — the M2 in-memory limiter is
      per-process; multi-replica deploys need shared state, and denylisting rotated refresh tokens
      makes rotation airtight against replay. (Needs a redis client wired into app.state.)
- [ ] **Frontend component tests** (Vitest + Testing Library) for auth, upload→poll, chat stream.
- [ ] **Worker autoscaling on queue depth** (KEDA ScaledObject vs Redis list length) instead of CPU.
- [ ] **Transactional outbox** for enqueue (replaces commit-before-enqueue with an atomic guarantee).
- [ ] **Alembic autogenerate check in CI** (fail if models drift from migrations).
- [ ] **Image + dependency scanning** in CI (Trivy, Dependabot/Renovate).

## Tier 3 — product features (larger)

- [ ] **PDF export** of incident reports (pandoc/WeasyPrint over the existing markdown).
- [ ] **Persisted RAG chunk index** in Qdrant (today the chat index is ephemeral per request).
- [ ] **LLM-backed agents** implementing the existing `Agent` protocol for richer investigation
      narratives (rules-based agents ship today).
- [ ] **Confidence calibration** heuristic (evidence coverage + group size + model self-report),
      tunable once eval data exists.
- [ ] **Live log streaming** sources (K8s pods / Docker / tail) behind a `LogSource` interface —
      the original brief's "future" items.
- [ ] **Similar-incident backfill** task for analyses created before M5.
- [ ] **Per-user storage quota** beyond per-file size caps.
- [ ] **Eval harness** for prompts/agents (regression tests on seeded incidents with known answers).

## Tier 4 — ops / polish

- [ ] TLS on the ingress (cert-manager); tighten CORS if SPA is served cross-origin.
- [ ] StatefulSet + PVC for postgres/qdrant (manifests use emptyDir for demo).
- [ ] Sealed-secrets / external-secrets operator instead of raw K8s Secrets.
- [ ] Structured request-ID propagation into logs (middleware) for cross-service tracing.
- [ ] OpenAPI-generated frontend client (hand-written today; worth it if the API triples).
