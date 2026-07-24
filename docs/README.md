# AI Log Analyzer — Documentation

Enterprise documentation set for the AI Log Analyzer platform. Every document is derived from the
actual source code and configuration; anything not directly implemented is explicitly marked
**(Inference)**.

> This is the numbered **handover documentation set**. It complements — and cross-references —
> the pre-existing build-history docs (`docs/modules/`, `docs/adr/`, `docs/planning/`,
> `docs/guides/`, `docs/portfolio/`). Where deep detail already exists there, these documents link
> to it rather than duplicating it.

## Reading order

| # | Document | Audience |
|---|----------|----------|
| 01 | [Project Overview](01_Project_Overview.md) | Everyone |
| 02 | [High-Level Architecture](02_High_Level_Architecture.md) | Architects, engineers |
| 03 | [Low-Level Design](03_Low_Level_Design.md) | Engineers |
| 04 | [Request Flow](04_Request_Flow.md) | Engineers |
| 05 | [API Documentation](05_API_Documentation.md) | API consumers, frontend |
| 06 | [Database Design](06_Database_Design.md) | Engineers, DBAs |
| 07 | [AI Architecture](07_AI_Architecture.md) | AI engineers |
| 08 | [DevOps & Deployment](08_DevOps_Deployment.md) | DevOps, SRE |
| 09 | [Security](09_Security.md) | Security, engineers |
| 10 | [Performance & Scaling](10_Performance_and_Scaling.md) | SRE, architects |
| 11 | [Testing](11_Testing.md) | Engineers, QA |
| 12 | [Operations Runbook](12_Operations_Runbook.md) | On-call, SRE |
| 13 | [Troubleshooting](13_Troubleshooting.md) | On-call, support |
| 14 | [Developer Guide](14_Developer_Guide.md) | New engineers |
| 15 | [User Guide](15_User_Guide.md) | End users |
| 16 | [Interview Guide](16_Interview_Guide.md) | Candidate/author |
| 17 | [Knowledge Transfer](17_Knowledge_Transfer.md) | Incoming team |
| 18 | [FAQ](18_FAQ.md) | Everyone |

## Diagrams

Mermaid source lives in [`diagrams/`](diagrams/) and is embedded inline throughout:
[architecture](diagrams/architecture.mmd) · [sequence](diagrams/sequence.mmd) ·
[erd](diagrams/erd.mmd) · [ai_pipeline](diagrams/ai_pipeline.mmd) ·
[deployment](diagrams/deployment.mmd) · [ci_cd](diagrams/ci_cd.mmd).

## Related existing documentation

- **Module build history:** [`docs/modules/`](modules/) (per-milestone "as-built" explainers)
- **Architecture decisions:** [`docs/adr/`](adr/)
- **Planning:** [`docs/planning/`](planning/) — requirements, architecture, roadmap, risk register, backlog
- **Guides:** [`docs/guides/`](guides/) — deployment, developer, user
- **Portfolio:** [`docs/portfolio/`](portfolio/) — system design, interview Q&A, related work

## Conventions

- **(Inference)** marks any statement not directly backed by code.
- Code references use repo-relative paths, e.g. `backend/app/services/pipeline.py`.
- All diagrams are Mermaid; they render on GitHub and in most Markdown viewers.
