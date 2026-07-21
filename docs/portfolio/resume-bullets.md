# Resume Bullets — AI Log Analyzer

Pick 3–5. Each is quantified and maps to real code in this repo.

## AI Engineer angle

- Built an AI log-analysis platform delivering root-cause diagnosis, plain-language explanations,
  and remediation for application/infra logs; **cut the cost of LLM analysis to near-zero on
  repeated errors** via content-fingerprint deduplication and a per-user insight cache.
- Designed a **three-layer prompt-injection defense** (data fencing, delimiter scrubbing, and a
  deny-by-default command allow-list) treating log content as untrusted input — verified with
  adversarial tests that neutralize `rm -rf` and shell-chaining attempts.
- Implemented **grounded RAG chat** over raw logs with code-level refusal: when retrieval scores
  fall below threshold the system declines *without calling the LLM*, eliminating a class of
  hallucinations; answers cite exact log line ranges.
- Built a **budgeted multi-agent investigation** (planner → investigator → verifier) with a
  persisted, inspectable step trace and a verifier that refuses to assert causation without
  temporal evidence.

## Backend / Platform angle

- Architected a **modular-monolith FastAPI service** (clean architecture, repository pattern, DI)
  with async SQLAlchemy, Celery background jobs behind a `202 Accepted` + polling pattern, and
  every external dependency (LLM, queue, embeddings, vector store) behind a swappable interface —
  enabling a **99-test suite that runs fully offline** with zero API calls or infrastructure.
- Implemented **JWT auth with refresh rotation, bcrypt hashing, rate limiting, audit logging**, and
  user-scoped data isolation enforced (and tested) at the vector-store and query layers.
- Streamed AI responses to the browser over **Server-Sent Events**, and shipped Prometheus RED
  metrics with high-cardinality-safe route templating.

## DevOps angle

- Containerized the full stack (multi-stage, non-root images) with **Docker Compose** and
  production **Kubernetes manifests** (Deployment/Service/Ingress/HPA/ConfigMap/Secret), plus
  Prometheus + Grafana monitoring, alerting rules, and a Locust load test targeting 100 concurrent
  users at p95 < 300ms on non-AI endpoints.
- Enforced quality with **GitHub Actions CI** (ruff/black/mypy/pytest), pre-commit hooks,
  conventional commits, ADRs, and a living risk register.

## One-line summary

> Production-grade AI platform (FastAPI + React + Celery + Qdrant, K8s-deployed) that diagnoses log
> incidents end to end — classification, root cause, grounded chat, multi-agent investigation —
> with security-first LLM integration and a 99-test offline suite.
