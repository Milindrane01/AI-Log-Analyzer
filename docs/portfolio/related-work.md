# Related Work

This project is a from-scratch **engineering** implementation of a problem that is also an active
**research** area (LLM-based log analysis and incident root-cause analysis). It is not a novel
research contribution, but it independently arrives at several ideas that the literature validates
— which is worth knowing when discussing the project in interviews or a write-up.

> Venues/years below are best-effort; verify before formal citation. Links were current as of
> mid-2025.

## Closest end-to-end systems

- **RCACopilot — "Automatic Root Cause Analysis via Large Language Models for Cloud Incidents"**
  (Chen et al., Microsoft, *EuroSys 2024*).
  On-call system that matches incidents to handlers, aggregates diagnostics, predicts a root-cause
  category, and generates an explanatory narrative — the research analog of our
  classify → root-cause → explain pipeline. Evaluated on a year of real Microsoft incidents.
  <https://dl.acm.org/doi/10.1145/3627703.3629553>

- **RCAgent — "Cloud Root Cause Analysis by Autonomous Agents with Tool-Augmented LLMs"**
  (Wang et al., Alibaba, *CIKM 2024*).
  Tool-augmented autonomous agent with action-trajectory self-consistency, run on a privately
  deployed model — the analog of our multi-agent investigation (M9).
  <https://arxiv.org/html/2310.16340v3>

## Agentic RCA (maps to our planner/investigator/verifier)

- **"Exploring LLM-based Agents for Root Cause Analysis"** (Roy et al., Microsoft, *FSE 2024*).
  <https://arxiv.org/pdf/2403.04123>
- **Auditable Graph-Guided RCA for Kubernetes Incidents** — "auditable/inspectable" mirrors our
  persisted, inspectable agent trace. <https://arxiv.org/html/2606.08590>

## Foundations we build on

- **Drain** (He et al., *ICWS 2017*) — fixed-depth-tree online log parser. Our fingerprinting uses
  the same idea: strip variable tokens → stable template.
- **DeepLog** (Du et al., *CCS 2017*), **LogBERT** (Guo et al., 2021) — learned log-anomaly detection.
- **RAG** (Lewis et al., *NeurIPS 2020*) — retrieval-augmented generation, the basis of our chat.
- **OWASP Top 10 for LLM Applications** — "LLM01: Prompt Injection" maps directly to our fencing +
  allow-list command design.
- **ReAct** (Yao et al., 2022) / **Reflexion** (Shinn et al., 2023) — reasoning + verification loops,
  echoed by our verifier agent.

## How our implementation compares

| Idea in our project | Prior work | Note |
|---|---|---|
| Fingerprint-group errors before the LLM | Drain-style parsing | Applied as a *cost* lever for LLM calls |
| Grounded chat with code-level refusal | RAG + grounding literature | Refuses without an LLM call — a stricter guarantee |
| Allow-listed remediation commands | OWASP LLM01 | Safety **by construction**, not by output filtering |
| Planner/investigator/verifier + trace | RCAgent, Roy et al. | Rules-based agents; LLM agents are a drop-in via the `Agent` protocol |
| Fully offline, mock-provider test suite | — | A reproducibility strength most systems papers lack |

**If pursuing a paper:** the realistic path is a narrow, well-evaluated claim (e.g. the
dedup-before-LLM cost/quality tradeoff, or allow-list injection-resistance) benchmarked on public
log datasets (Loghub) against baselines — not "better RCA than Microsoft." See
[the backlog](../planning/05-backlog.md) and ask for a research-directions plan.
