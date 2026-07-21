"""Load test. Run against a running stack:

    pip install locust
    locust -f tests/performance/locustfile.py --host http://localhost:8000

Target (from NFRs): 100 concurrent users, API p95 < 300ms for non-AI endpoints.
Each simulated user registers once, then loops paste → poll → browse groups —
the real hot path. AI analysis is async (202), so the API stays fast even when
the worker is busy; that's the design being validated here.
"""

import uuid

from locust import HttpUser, between, task

SAMPLE_LOG = (
    "2026-07-15 10:12:14 ERROR Database connection timeout for user 8231\n"
    "2026-07-15 10:12:15 WARNING Slow query took 2140 ms\n"
) * 20


class LogAnalystUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        email = f"load-{uuid.uuid4().hex[:12]}@example.com"
        creds = {"email": email, "password": "a-long-passphrase"}
        self.client.post("/api/v1/auth/register", json=creds)
        tokens = self.client.post("/api/v1/auth/login", json=creds).json()
        self.headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    @task(3)
    def paste_and_poll(self) -> None:
        resp = self.client.post(
            "/api/v1/logs/paste", json={"content": SAMPLE_LOG}, headers=self.headers
        )
        if resp.status_code == 202:
            aid = resp.json()["analysis_id"]
            self.client.get(f"/api/v1/analyses/{aid}", headers=self.headers, name="/analyses/[id]")

    @task(2)
    def browse_history(self) -> None:
        self.client.get("/api/v1/analyses?limit=20", headers=self.headers)

    @task(1)
    def health(self) -> None:
        self.client.get("/api/v1/health")
