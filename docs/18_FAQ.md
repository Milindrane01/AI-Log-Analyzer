# 18 — FAQ

## General

**What problem does this solve?**
It compresses the *diagnosis* phase of an incident — grouping, root-causing, explaining, and
suggesting fixes for logs — so MTTR drops. See [01 Project Overview](01_Project_Overview.md).

**Does it need OpenAI to run?**
No. Without `APP_OPENAI_API_KEY`, parsing, grouping, timelines, similarity (if Qdrant is set), and
reports still work; only AI insights and chat are disabled, and a mock provider powers a full
offline demo. See [07 AI Architecture](07_AI_Architecture.md).

**Is it production-ready?**
Feature-complete and well-tested, with documented hardening still in the backlog (shared rate
limiter, queue-depth autoscaling, backups, TLS). See
[`docs/planning/05-backlog.md`](planning/05-backlog.md).

## Architecture

**Why a modular monolith, not microservices?**
Microservices solve org-scaling this project doesn't have; module seams allow a later split.
[ADR-001](adr/001-modular-monolith.md).

**Why is analysis asynchronous?**
LLM calls take 10–60s; a synchronous request would time out and duplicate cost.
[ADR-002](adr/002-celery-for-ai-jobs.md).

**Why Qdrant and not FAISS/pgvector?**
Server-side payload filtering (per-user isolation), persistence, and an ops story.
[ADR-003](adr/003-qdrant-over-faiss.md).

## AI & safety

**How do you stop the AI from hallucinating in chat?**
Code-level refusal below a retrieval score threshold (no LLM call) plus mandatory line-range
citations. [07](07_AI_Architecture.md) / [09](09_Security.md).

**Can the AI suggest a dangerous command?**
No. Commands are rendered from an allow-listed catalog of read-only diagnostics with regex-validated
params — a destructive command has no template. Nothing is ever executed. [09 Security](09_Security.md).

**How is prompt injection handled?**
Log content is fenced as data, delimiter look-alikes scrubbed, output schema-validated, and commands
allow-listed. [09 Security](09_Security.md).

## Operations

**How do I deploy?**
Compose for local, Kubernetes for prod; always run `alembic upgrade head`.
[08 DevOps](08_DevOps_Deployment.md) / [`guides/deployment-guide.md`](guides/deployment-guide.md).

**An analysis is stuck — what do I check?**
Worker running? broker URL correct? worker logs? [13 Troubleshooting](13_Troubleshooting.md).

**How does it scale?**
Stateless API (HPA on CPU), workers scale on load (queue depth is the correct signal).
[10 Performance & Scaling](10_Performance_and_Scaling.md).

## Testing & quality

**How can 99 tests run with no API key or infra?**
Every dependency has a deterministic fake (LLM, queue, embeddings, vector store, DB).
[11 Testing](11_Testing.md).

## Research / portfolio

**Is this based on published research?**
It's an engineering implementation of an active research area; closest systems are RCACopilot and
RCAgent. See [`docs/portfolio/related-work.md`](portfolio/related-work.md).

**Could it become a paper?**
Only with a narrow, well-evaluated claim on public log benchmarks against baselines (e.g.
dedup-before-LLM cost/quality, or allow-list injection-resistance) — not "better RCA than
Microsoft." See [`docs/planning/05-backlog.md`](planning/05-backlog.md).

## Contributing

**What's the workflow?**
Feature branch → PR → CI green → squash; update module doc, `progress.md`, `CHANGELOG`, and
`.env.example` in the same PR. [14 Developer Guide](14_Developer_Guide.md) / `CONTRIBUTING.md`.
