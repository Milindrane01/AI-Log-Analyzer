# Interview Q&A — AI Log Analyzer

Talking points tied to real decisions in this codebase. Each module doc also ends with questions.

## System design

**Q: Why a modular monolith and not microservices?**
Microservices solve organizational scaling (many teams), which a solo/small project doesn't have.
They add network failure modes, distributed tracing, and deployment complexity for no benefit at
this size. Clean module boundaries keep the split-later option open — the seams (`ai/`, `workers/`)
*are* the future service boundaries. See ADR-001.

**Q: Why is AI analysis a background job instead of a synchronous request?**
LLM analysis takes 10–60s. Holding an HTTP request open that long fails at every layer — client
timeouts, proxy limits, thread starvation, and retries that double the LLM spend. The `202 Accepted`
+ polling pattern (Celery + Redis) decouples request latency from work duration. See ADR-002.

**Q: How do you keep LLM costs down?**
Analyze *grouped, deduplicated* errors, not raw lines (212 identical timeouts → one analysis);
cache insights by content fingerprint per user (repeat errors cost zero tokens); cap AI to the
top-N groups; tier models. The deterministic parsing/grouping in front of the LLM is the main lever.

## AI / security

**Q: Logs are attacker-controlled. How do you prevent prompt injection?**
Three layers: (1) fence log content in unique delimiters the system prompt declares inert; (2) scrub
delimiter look-alikes and cap length; (3) validate all output against a strict schema, and render
commands only from an allow-listed template catalog with regex-validated parameters. A model told to
emit `rm -rf /` has no template that produces it. Tested with adversarial inputs.

**Q: How do you stop the chat feature from hallucinating?**
Grounding is enforced in code, not just the prompt: if retrieval scores are below threshold, the
pipeline returns "I don't see that in this log" *without calling the LLM*. When it does answer, the
prompt requires line-range citations, and the UI shows them. Retrieval is lexical-first because
bag-of-words cosine drowns rare error terms under repeated noise lines.

**Q: When is multi-agent actually worth it?**
Rarely — most single-error analyses are already handled cheaply in one shot (M4). Multi-agent is for
multi-service cascades where one prompt can't hold the causal chain. It's justified only with hard
budgets (max steps, wall clock), a verifier that can reject a hypothesis, and a persisted trace so
the reasoning is inspectable. Without those it's a black box, not an engineering artifact.

## Backend

**Q: How is this testable without hitting OpenAI or spinning up infra?**
Every dependency is behind an interface with a fake: `LLMProvider`→mock, `TaskQueue`→inline runner,
`EmbeddingProvider`→hashing, `VectorStore`→in-memory, DB→SQLite. The 99-test suite runs offline in
~30s. This also caught real bugs deterministically (e.g. a commit-before-enqueue race that would be
intermittent with real Celery).

**Q: Liveness vs readiness — why two probes?**
Liveness = "process alive" → K8s restarts on failure. Readiness = "dependencies reachable" → K8s
stops routing but doesn't restart. Conflating them means a brief DB outage restarts every healthy
API pod at once, amplifying the incident.

**Q: How do you enforce tenant isolation?**
Every user-owned query filters by `user_id`; cross-user access returns 404, never 403 (no existence
leak). The vector store applies the `user_id` filter server-side. Both are covered by tests.

## DevOps

**Q: How would you autoscale the workers?**
CPU HPA is the portable default shipped here, but it lags the real signal. Workers should scale on
Celery queue depth (KEDA ScaledObject against the Redis list length) — that's the metric that
actually reflects backlog. Documented in `hpa.yaml`.

**Q: What's your monitoring strategy?**
RED method (Rate, Errors, Duration) per route via a `/metrics` endpoint, scraped by Prometheus,
visualized in Grafana, with alert rules for 5xx ratio, latency, and target-down. Paths are templated
(`/analyses/{id}`) to avoid high-cardinality metric explosions.
