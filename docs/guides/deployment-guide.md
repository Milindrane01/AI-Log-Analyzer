# Deployment Guide

## Local (Docker Compose)

```bash
cp backend/.env.example backend/.env      # set POSTGRES_PASSWORD, optionally APP_OPENAI_API_KEY
docker compose up --build
docker compose exec api alembic upgrade head   # apply migrations 001–006
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API + Swagger | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 (admin / `GRAFANA_PASSWORD`) |

Import `infra/monitoring/grafana-dashboard.json` into Grafana; point its datasource at Prometheus.

## Kubernetes (kind / minikube)

```bash
# 1. Build and load images into the cluster
docker build -t log-analyzer-api:latest      -f infra/docker/api.Dockerfile      backend
docker build -t log-analyzer-frontend:latest -f infra/docker/frontend.Dockerfile frontend
kind load docker-image log-analyzer-api:latest log-analyzer-frontend:latest   # or `minikube image load`

# 2. Secrets (never commit the filled file)
cp infra/k8s/secret.example.yaml infra/k8s/secret.yaml   # edit values

# 3. Apply
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml -f infra/k8s/secret.yaml
kubectl apply -f infra/k8s/data-stores.yaml
kubectl apply -f infra/k8s/api.yaml -f infra/k8s/worker.yaml -f infra/k8s/frontend.yaml
kubectl apply -f infra/k8s/ingress.yaml -f infra/k8s/hpa.yaml

# 4. Migrate (one-off)
kubectl -n log-analyzer exec deploy/api -- alembic upgrade head

# 5. Access (add `log-analyzer.local` to /etc/hosts → ingress IP)
kubectl -n log-analyzer get ingress
```

## Production checklist

- [ ] Real `APP_JWT_SECRET_KEY` (boot refuses the dev default in production — by design)
- [ ] Managed Postgres + backups; swap emptyDir stores for StatefulSet + PVC
- [ ] TLS on the ingress (cert-manager); tighten CORS if the SPA is served cross-origin
- [ ] Worker autoscaling on queue depth (KEDA + Redis) instead of CPU — see `hpa.yaml` note
- [ ] Secrets via sealed-secrets / external-secrets, not raw manifests
- [ ] Alertmanager wired to `infra/monitoring/alerts.yml`
- [ ] Dependency + image scanning in CI (Dependabot, Trivy)
