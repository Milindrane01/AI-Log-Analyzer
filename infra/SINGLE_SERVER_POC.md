# Single-Server POC — server spec, dependencies, and run steps

Run the **entire stack** (API, Celery worker, PostgreSQL, Redis, Qdrant, frontend/Nginx) on **one
EC2 instance** with Docker Compose. No Terraform required for this path — launch one EC2, install
Docker, clone, `docker compose up`.

> Where Terraform fits: Terraform *provisions* the EC2 from your laptop; it never runs on the target
> box. If you prefer Infrastructure-as-Code, use `infra/terraform/poc/` (see its README). Otherwise
> follow this manual runbook — it's the quickest for a single-server demo.

---

## 1. Server configuration (the EC2 to launch)

| Setting | Value | Why |
|---|---|---|
| OS | **Ubuntu 24.04 LTS** | matches our images/tooling |
| Instance type | **t3.large** (2 vCPU, **8 GB RAM**) | 7 containers on one host; 8 GB gives headroom |
| Storage | **40 GB gp3** | images + Postgres/Qdrant data + uploads |
| Public IP | **Yes** (Elastic IP recommended) | reach the app |
| Architecture | x86_64 (amd64) | our images are amd64 |

Sizing notes:
- The default deploy uses `APP_EMBEDDING_BACKEND=hashing` (no PyTorch), so **8 GB is enough**.
- If you switch to `APP_EMBEDDING_BACKEND=sentence-transformers`, that pulls PyTorch (~2 GB) into the
  worker — use **t3.xlarge (16 GB)**.
- `t3.medium` (4 GB) will be tight/OOM with all services; avoid for the full stack.

### Security group (inbound)

| Port | Source | Purpose |
|---|---|---|
| 22 | **your IP /32** | SSH |
| 80 | 0.0.0.0/0 | app (frontend) |
| 8000 | your IP /32 (optional) | direct API/Swagger while testing |

**Do NOT open** 5432 (Postgres), 6379 (Redis), 6333 (Qdrant) — they stay on the internal Docker
network.

---

## 2. Dependencies to install ON the server

Only three things — everything else runs in containers (no Python, Node, Postgres, Redis on the
host):

- **Docker Engine**
- **Docker Compose plugin**
- **git**

```bash
# SSH in first:  ssh ubuntu@<EC2_PUBLIC_IP>
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg git

# Docker's official repo + engine + compose plugin
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# run docker without sudo
sudo usermod -aG docker ubuntu && newgrp docker
docker --version && docker compose version
```

---

## 3. Get the code onto the server

Either clone from GitHub:
```bash
cd ~ && git clone https://github.com/<you>/AI-Log-Analyzer.git ai-log-analyzer
cd ai-log-analyzer
```
…or let the GitHub Actions workflow (`.github/workflows/deploy.yml`) copy it on every push to `main`
(then you only do steps 1–2 once, by hand).

---

## 4. Create `backend/.env`

```bash
cat > backend/.env <<'EOF'
APP_ENVIRONMENT=production
APP_LOG_JSON=true
APP_JWT_SECRET_KEY=change-me-to-a-long-random-string
APP_OPENAI_API_KEY=            # leave empty to run without AI (mock demo)
APP_DATABASE_URL=postgresql+asyncpg://loganalyzer:poc-db-password@postgres:5432/loganalyzer
APP_REDIS_URL=redis://redis:6379/0
APP_QDRANT_URL=http://qdrant:6333
APP_UPLOAD_DIR=/srv/uploads
APP_EMBEDDING_BACKEND=hashing
POSTGRES_USER=loganalyzer
POSTGRES_PASSWORD=poc-db-password
POSTGRES_DB=loganalyzer
GRAFANA_PASSWORD=admin
EOF
```

Generate a real secret: `openssl rand -hex 32`.

---

## 5. Serve the frontend on port 80

The committed `docker-compose.yml` maps the frontend to host **3000**. For port 80, add an override
(no need to edit the original file):

```bash
cat > docker-compose.override.yml <<'EOF'
services:
  frontend:
    ports:
      - "80:80"
EOF
```

(Or open port 3000 in the security group and use `http://<ip>:3000` instead.)

---

## 6. Run it

```bash
docker compose up -d --build
docker compose exec -T api alembic upgrade head    # apply DB migrations
docker compose ps                                  # all services "Up"/"healthy"
```

Open **http://<EC2_PUBLIC_IP>** → register → paste a log. API docs at
`http://<EC2_PUBLIC_IP>:8000/docs` (if you opened 8000).

---

## 7. Verify & operate

```bash
curl -s http://localhost:8000/api/v1/health           # {"status":"ok",...}
curl -s http://localhost:8000/api/v1/health/ready      # database/vector_store checks
docker compose logs -f worker                          # watch analyses process
docker compose down                                    # stop
docker compose up -d --build                           # redeploy after code changes
```

---

## If you DO want Terraform (from your laptop, not the server)

Terraform needs AWS credentials. Install on **your machine** (or a small bootstrap box), then:

```bash
aws configure          # paste Access Key ID + Secret (IAM user with EC2/VPC/EIP perms)
cd infra/terraform/poc
cp terraform.tfvars.example terraform.tfvars   # set ssh_public_key + ssh_allowed_cidr
terraform init && terraform apply              # creates the EC2 with Docker preinstalled
terraform output public_ip                     # → SSH in, then do steps 3–6 above
```

The Terraform `user_data.sh` already installs Docker, so on a Terraform-created box you skip step 2.

---

## Common blockers (and fixes)

| Symptom | Fix |
|---|---|
| `permission denied` on docker | `sudo usermod -aG docker ubuntu` then re-login (`newgrp docker`) |
| Worker OOM / analyses stuck | instance too small — use t3.large (8 GB); keep `hashing` embedder |
| App boots then 500s | `APP_JWT_SECRET_KEY` unset in production — set a real one |
| Can't reach app on :80 | add the `docker-compose.override.yml` (step 5) and open port 80 in the SG |
| Migrations error | run `docker compose exec -T api alembic upgrade head` after `up` |
| Chat returns 503 | no `APP_OPENAI_API_KEY` — expected; everything else still works |

See also [`docs/13_Troubleshooting.md`](../docs/13_Troubleshooting.md) and
[`docs/guides/aws-deployment.md`](../docs/guides/aws-deployment.md).
