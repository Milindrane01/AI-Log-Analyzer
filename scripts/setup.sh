#!/usr/bin/env bash
# One-shot local dev setup (macOS/Linux). Run from project root: bash scripts/setup.sh
set -euo pipefail

command -v python3 >/dev/null || { echo "MISSING: python3 (3.12+)"; exit 1; }
command -v node >/dev/null || { echo "MISSING: node (20+)"; exit 1; }

echo "== Backend: venv + dependencies =="
cd backend
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -e ".[dev]"
[ -f .env ] || { cp .env.example .env; echo ">> Created backend/.env — edit POSTGRES_PASSWORD"; }
cd ..

echo "== Frontend: node_modules =="
cd frontend && npm install --no-audit --no-fund && cd ..

echo "== Verify: backend tests =="
cd backend && ./.venv/bin/python -m pytest -q && cd ..

echo "Done. Run: docker compose up --build  ->  http://localhost:3000"
