# Module 10 — Production Hardening & Deployment

> **Status:** ✅ Built (2026-07-20) · 99/99 backend tests · **project feature-complete**
> Depends on: everything · Final milestone

## As built — deviations from plan & key notes

- **Hand-rolled Prometheus metrics** (`app/core/metrics.py`), no prometheus_client dependency —
  the text format is trivial and consistency with the "thin over vendor SDK" philosophy matters.
  RED method per route; paths templated (`/analyses/{id}`) to avoid high-cardinality series
  explosion — a real production footgun, guarded by a test.
- **K8s manifests target kind/minikube** but are production-shaped: liveness/readiness split,
  resource requests/limits, HPA, config/secret separation. `emptyDir` stores are called out as
  demo-only with the StatefulSet+PVC upgrade documented.
- **HPA on CPU with an honest note**: workers *should* scale on Celery queue depth (KEDA+Redis);
  CPU is the portable default that runs on a vanilla cluster. The gap is documented, not hidden.
- **Locust load test** models the real hot path (register → paste → poll → browse), validating
  that the `202`+poll design keeps the API fast even while workers are busy.
- Full monitoring stack in compose (Prometheus + Grafana + alert rules + dashboard).
- PDF export (M8) and a persisted RAG chunk index (M7) remain the two documented, deliberate
  deferrals — everything in the original brief's 10 AI phases is delivered.

## Goal

"Works in compose" becomes "deployed, observable, scalable, documented." This module is what
separates a portfolio project from a tutorial project in interviews.

## What gets built

- [ ] Kubernetes manifests: Deployment (api, worker, frontend), Service, Ingress,
      ConfigMap, Secret, HPA (CPU + queue-depth scaling for workers)
- [ ] Production Dockerfile variants (multi-arch, pinned digests, no dev deps)
- [ ] Prometheus: FastAPI metrics middleware (latency histograms, request counts),
      Celery queue metrics, LLM token/cost counters
- [ ] Grafana dashboards: API health, queue depth, AI cost per day, error rates
- [ ] Alerting rules: readiness failures, queue backlog, cost budget breach
- [ ] Performance tests (locust): 100 concurrent users target, documented results
- [ ] Security pass: dependency audit, secret scanning in CI, security headers, CORS tightening
- [ ] Docs: deployment guide, developer guide, user guide, system design explanation
- [ ] Resume bullets + interview Q&A pack generated from the actual build history

## Key concepts you'll learn

K8s resource model end-to-end; HPA on custom metrics (queue depth — the right signal for
workers); RED/USE monitoring methodology; SLOs and error budgets; load-testing methodology;
supply-chain security basics.

## Planned files

`infra/k8s/*.yaml`, `infra/monitoring/{prometheus,grafana}/`, `app/core/metrics.py`,
`tests/performance/locustfile.py`, `docs/{deployment,developer,user}-guide.md`

## Acceptance criteria (demo)

`kubectl apply` brings the stack up on a local cluster (kind/minikube); Grafana shows live
traffic; killing a pod self-heals; HPA scales workers under load; the load-test report and
resume bullets are in `docs/`.
