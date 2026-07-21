# Requirements & Scope — AI Log Analyzer

> Module 0 deliverable. Owner: TG. Status: Draft v1 (2026-07-16)

## 1. Problem Statement

When production breaks, engineers face thousands of raw log lines across services. Finding the
root cause requires expertise, context, and time — the three things you have least of during an
incident. Mean-time-to-resolution (MTTR) is dominated not by *fixing* but by *diagnosing*.

**The product:** a platform that ingests logs, groups and classifies errors, identifies probable
root causes, explains them in plain language, and recommends concrete remediation steps —
reducing diagnosis time from hours to minutes.

## 2. Target Users (Personas)

| Persona | Pain point | What they need |
|---|---|---|
| **SRE on-call** | Paged at 3am, unfamiliar service | Fast triage: severity, root cause, next command to run |
| **DevOps engineer** | Repeated incidents across environments | Dedup/grouping, similar-incident history, K8s/AWS runbooks |
| **Backend developer** | Cryptic stack traces, unfamiliar infra errors | Plain-language explanations, suggested fixes |
| **Junior engineer** | Lacks pattern recognition of a senior | Beginner-friendly explanations, learning from history |

## 3. User Stories (Core)

- As an SRE, I upload a log file and get a ranked list of error groups with severity within seconds.
- As a developer, I paste a stack trace and get a plain-language explanation with a confidence score.
- As a DevOps engineer, I see suggested `kubectl`/`systemctl`/AWS commands for a diagnosed issue.
- As an on-call, I search past analyses for similar incidents ("have we seen this before?").
- As a team lead, I generate an incident report from an analysis for the postmortem.
- As a user, I chat with my uploaded logs ("what happened between 10:12 and 10:15?").
- As an admin, I know all access is authenticated and audit-logged.

## 4. Functional Requirements

### FR-1 Ingestion
- FR-1.1 Upload log files (txt/log/json, size-limited, validated)
- FR-1.2 Paste raw log text
- FR-1.3 *(Future)* Stream from Kubernetes pods / Docker containers / real-time tail

### FR-2 Processing Pipeline
- FR-2.1 Detect log format (syslog, JSON, logfmt, common app formats, unknown/freeform)
- FR-2.2 Parse into structured entries (timestamp, level, message, source, metadata)
- FR-2.3 Group duplicate/similar errors (fingerprinting)
- FR-2.4 Classify severity (Critical / High / Medium / Low / Info)

### FR-3 AI Analysis (delivered in phases — see roadmap)
- FR-3.1 Error classification (type taxonomy: DB, network, auth, resource, app logic, …)
- FR-3.2 Root cause analysis with possible-reasons list
- FR-3.3 Plain-language summarization
- FR-3.4 Similar incident search (embeddings)
- FR-3.5 Chat with uploaded logs (RAG)
- FR-3.6 Auto-generated incident report
- FR-3.7 Suggested shell / Kubernetes / AWS remediation commands
- FR-3.8 Incident timeline reconstruction
- FR-3.9 Multi-agent investigation
- FR-3.10 Confidence score on every AI output

### FR-4 Platform
- FR-4.1 User registration/login (JWT)
- FR-4.2 Analysis history per user (paginated)
- FR-4.3 Audit log of security-relevant actions

## 5. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | API p95 < 300ms for non-AI endpoints; AI analysis async with job status |
| Scale (design target) | 100 concurrent users, log files up to 50MB, 1M entries/file |
| Security | JWT auth, rate limiting, input validation, prompt-injection defenses, secrets via env |
| Reliability | Graceful LLM-failure degradation (never lose the upload); retries with backoff |
| Cost | Token budgets per analysis; cache identical analyses; cheap model for cheap tasks |
| Observability | Structured logging, Prometheus metrics, health/readiness endpoints |
| Quality | Type-checked (mypy), linted (ruff), tested (pytest, >80% on core logic), CI-gated |
| Portability | Runs via docker-compose locally; K8s manifests for production |

## 6. Explicitly Out of Scope (v1)

- Live log streaming and agent-based collection (design for it, don't build it)
- Multi-tenancy / organizations / RBAC beyond user-owns-their-data
- Auto-*execution* of remediation commands (we only **suggest** — executing is a safety boundary)
- Mobile UI

## 7. Key Risks

| Risk | Mitigation |
|---|---|
| LLM hallucinates root causes | Confidence scores, structured outputs, show evidence lines, never auto-execute |
| Prompt injection via log content | Logs are *data*, never instructions: delimiter fencing, output schema validation, allow-listed command templates |
| Token costs explode on big files | Analyze error groups (not raw lines), truncation strategy, caching |
| Scope creep (10 AI phases) | Strict milestone gates; each phase ships independently |
