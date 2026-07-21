# Module 8 — Remediation & Incident Reports (Phases 6–8)

> **Status:** ✅ Built (2026-07-18) · 86/86 backend tests + frontend typecheck
> Depends on: Module 4 · Delivers AI Phases: 6 (incident report), 7 (shell commands), 8 (K8s fixes)

## As built — deviations from plan & key notes

- **Allow-list the STRUCTURE, not just filter output** (stronger than M4): the model never emits
  shell. It would pick a template id + params; we render from OUR template with OUR regex-validated
  params. A namespace can only match `[a-z0-9-]` — `prod; rm -rf /` is rejected at substitution.
  A template that produces `rm -rf` simply doesn't exist in the catalog.
- **M8 selector is deterministic** (error_type → template ids), no extra LLM call — cheap,
  reliable, trivially testable. An LLM selector can slot in behind `suggest_commands()` later,
  still constrained to template-id + params output.
- **`test_every_catalog_template_is_read_only`** scans the whole catalog for mutating verbs
  (delete/restart/apply/scale/kill/...) — a standing guard so nobody adds a dangerous template.
- **Report is deterministic assembly**, not a new LLM call — the AI spend happened in M4; the
  report composes existing insights + commands into postmortem markdown. Fast, free, reproducible.
- Report is idempotent per analysis (regenerate updates in place); markdown download via
  `Content-Disposition`. PDF export deferred — markdown covers the portfolio need and renders
  everywhere; a pandoc/weasyprint step is a documented add-on.

## Goal

Close the loop from diagnosis to action: concrete, safe remediation commands (Linux, kubectl,
AWS) and a postmortem-ready incident report generated from an analysis.

## What gets built

- [x] Allow-listed command templates: catalog of 13 read-only templates, id+params rendering
- [x] Command catalog per domain (linux/kubernetes/aws) with "what it checks" descriptions
- [x] Regex parameter validation before substitution (injection rejected at the boundary)
- [x] Read-only-only in M8; `mutating` field reserved; catalog-wide read-only guard test
- [x] `IncidentReport` model (migration 005) + `POST /analyses/{id}/report`
- [x] Report sections: summary, impact, findings (per group), prevention
- [x] Markdown export (`GET .../report.md`); PDF deferred (documented)
- [x] Report panel + generate button + download link on the analysis page
- [x] Tests: template injection, param escaping, read-only guard, report structure, idempotency

## Key concepts you'll learn

Why allow-listing beats sanitizing for LLM-generated commands (deny-by-default security);
the suggest-vs-execute boundary as product safety design; templated generation as a
hallucination defense; document generation pipelines.

## Planned files

`app/ai/commands/catalog/{linux,k8s,aws}.py`, `app/ai/commands/selector.py`,
`app/services/report.py`, `app/models/report.py`, `app/api/v1/reports.py`

## Acceptance criteria (demo)

DB-timeout analysis → suggested commands exactly match catalog templates with validated
parameters; a prompt-injected log cannot smuggle `rm -rf` into suggestions; one click produces
a postmortem PDF.
