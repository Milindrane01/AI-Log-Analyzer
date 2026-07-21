# Module 4 — First AI Analysis (Phases 1–3)

> **Status:** ✅ Built (2026-07-18) · 56/56 total tests passing
> Depends on: Module 3 · Delivers AI Phases: 1 (classification), 2 (root cause), 3 (summarization)

## As built — deviations from plan & key notes

- **OpenAI via raw httpx, not the SDK** — one endpoint + strict `json_schema` response_format;
  flat dependency tree, fully visible request (token spend debuggable). Provider seam means
  swapping to the SDK later is one file.
- **Three-layer injection defense** (`ai/guards/injection.py`): fence with unique delimiters +
  system-prompt rule; scrub fence look-alikes and cap length; deny-by-default command allow-list
  (read-only diagnostics only — `kubectl get/describe/logs`, `systemctl status`, never
  delete/restart/apply). Tests prove `rm -rf /`, chaining (`;`, `&&`, `|`) and mutations are dropped.
- **Fingerprint cache in postgres, not redis** — insight reuse is keyed (user_id, fingerprint):
  same error next week = zero tokens. `from_cache` flag surfaces it in the API. Redis response
  cache still available later as a hot layer.
- **Graceful degradation is tested**: provider outage → analysis still COMPLETED with groups,
  insights absent; a UI state, not an error.
- **AI refines severity**: M3's level heuristic (error→high) is overridden by content
  understanding (DB connectivity → critical) — asserted in tests.
- **Confidence is model-reported with prompt guidance** (0.9+ only for textbook signatures);
  the calibration-heuristic blend from the plan is deferred until we have eval data to tune it.
- Cost caps: only top-10 groups per analysis get AI; temperature 0.2; cheap model default.

## Goal

The product's core promise: each error group gets an error type, severity, root cause,
plain-language explanation, suggested fix, and confidence score — the brief's example
(DB timeout → "Database Connectivity, Critical, 94%") becomes real.

## What gets built

- [x] `LLMProvider` interface + OpenAI implementation (timeout, token accounting; retries via Celery)
- [x] Structured outputs: strict json_schema → Pydantic validation — parse failures are LLMError
- [x] Versioned prompt template (`analysis-v1`) with few-shot example + confidence guidance
- [x] Prompt-injection guards: fencing, scrubbing, deny-by-default command allow-list
- [x] Model tiering config (cheap/strong); M4 uses cheap for all — strong reserved for M9 agents
- [x] Fingerprint-keyed insight cache (postgres) — identical error → zero-cost analysis
- [x] Token usage stored per insight (prompt/completion) — cost queryable per analysis
- [x] Graceful degradation: LLM outage → analysis COMPLETED, groups without insights
- [x] `MockLLMProvider` — full suite runs offline; also powers keyless demo mode
- [~] Confidence: model-reported + prompt guidance (calibration heuristic deferred until evals)

## Key concepts you'll learn

Why structured output beats free-text parsing; prompt versioning as code; injection defenses
for untrusted text (logs are attacker-controlled input!); cost engineering (tiering, caching,
truncation); testing AI systems with deterministic mocks; evals as regression tests for prompts.

## Planned files

`app/ai/providers/base.py`, `app/ai/providers/openai.py`, `app/ai/providers/mock.py`,
`app/ai/prompts/classification.py`, `app/ai/prompts/root_cause.py`, `app/ai/pipelines/analyze.py`,
`app/ai/guards/injection.py`, `app/schemas/analysis.py`, `tests/unit/test_ai_pipeline.py`

## Acceptance criteria (demo)

Paste the brief's example log → response matches the brief's expected output shape (error type,
severity, root cause, possible reasons, recommended commands placeholder, confidence). Tests
pass offline with the mock provider; a poisoned log line ("ignore previous instructions…") is
neutralized.
