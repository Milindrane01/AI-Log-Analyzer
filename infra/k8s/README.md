# Kubernetes manifests

Apply order (namespace → config → data → app):

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.example.yaml    # copy to secret.yaml, fill real values, DON'T commit
kubectl apply -f postgres.yaml -f redis.yaml -f qdrant.yaml
kubectl apply -f api.yaml -f worker.yaml -f frontend.yaml
kubectl apply -f ingress.yaml -f hpa.yaml
```

These target a local cluster (kind/minikube) but are structured like production:
liveness/readiness probes, resource requests/limits, HPA, secrets separate from config.
For a managed cluster, swap the `emptyDir`/`hostPath` volumes for a real StorageClass.
