# Risk Register — living document

> Reviewed at the start of every module. Likelihood/Impact: L / M / H.
> A risk without a trigger and response is a worry, not a managed risk.

| ID | Risk | L | I | Mitigation (doing now) | Trigger → response | Status |
|----|------|---|---|------------------------|--------------------|--------|
| R1 | LLM hallucinates root causes users act on | M | H | Confidence scores, structured outputs, evidence lines shown, commands never auto-executed | User reports wrong diagnosis → add eval case, tune prompt, lower confidence display | Open |
| R2 | Prompt injection via uploaded log content | H | H | Logs fenced as data; output schema validation; allow-listed command templates (M8) | Injection found in testing → add to guard test suite, patch guard | Open |
| R3 | LLM API cost blowout | M | M | Analyze groups not lines; model tiering; content-hash caching; per-user budgets | Daily cost > threshold → alert (M10), reduce tier, cap uploads | Open |
| R4 | Scope creep across 10 AI phases stalls delivery | H | M | Strict milestone gates; "out of scope" section on every issue; one module in progress at a time | Module exceeds 2× estimate → cut scope to acceptance criteria, defer rest | Open |
| R5 | Solo-developer burnout / abandonment | M | H | Small demo-able milestones; tracker shows visible progress; each module independently valuable on a resume | Two weeks without a commit → shrink next deliverable to one PR | Open |
| R6 | Secrets leak (API keys in repo) | L | H | .gitignore on .env, detect-private-key pre-commit hook, `${VAR:?}` compose guards | Key committed → rotate immediately, purge history, add CI secret scan (M10 pulls earlier) | Open |
| R7 | Learning curve (FastAPI new to TG) slows modules | M | L | Full mentor mode; module docs double as study notes; interview Qs per module | Concept blocking > 1 session → dedicated deep-dive before continuing | Open |
| R8 | Sandbox/tooling friction (git, mounts) corrupts repo | M | M | Git operations run on user's machine only; sandbox verifies via tests | Mount write anomaly → verify with `find`/hashes, rewrite affected file | Open |
| R9 | Big uploads (50MB) break memory/timeouts | M | M | Streaming uploads, size caps, async parsing (M3 design) | OOM/timeout in testing → chunked parsing, tighter caps | Open |
| R10 | OpenAI API changes/deprecations mid-project | L | M | Provider interface isolates SDK; pinned versions; mock provider keeps CI green | Breaking change → adapt one file (`ai/providers/openai.py`) | Open |

## Accepted (no action)

- Python 3.10 in dev sandbox vs 3.12 target — CI enforces 3.12; sandbox only smoke-tests logic.
- evlog contributor skills in `.claude/skills/` — harmless; delete or replace locally at will.

## Retired

_None yet._
