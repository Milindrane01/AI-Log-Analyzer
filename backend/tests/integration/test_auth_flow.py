"""End-to-end auth flow through the real app stack (SQLite-backed)."""

from httpx import AsyncClient

CREDS = {"email": "sre@example.com", "password": "a-long-passphrase"}


async def _register(client: AsyncClient) -> dict:
    resp = await client.post("/api/v1/auth/register", json=CREDS)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_register_login_me(client: AsyncClient) -> None:
    user = await _register(client)
    assert user["email"] == CREDS["email"]
    assert "hashed_password" not in user  # storage details never leak

    login = await client.post("/api/v1/auth/login", json=CREDS)
    assert login.status_code == 200
    tokens = login.json()

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == user["id"]


async def test_duplicate_email_conflicts(client: AsyncClient) -> None:
    await _register(client)
    resp = await client.post("/api/v1/auth/register", json=CREDS)

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


async def test_wrong_password_is_401_with_generic_message(client: AsyncClient) -> None:
    await _register(client)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": CREDS["email"], "password": "wrong-password"}
    )

    assert resp.status_code == 401
    # Same message as unknown email — no user enumeration.
    assert "Invalid email or password" in resp.json()["error"]["message"]


async def test_refresh_rotates_pair(client: AsyncClient) -> None:
    await _register(client)
    tokens = (await client.post("/api/v1/auth/login", json=CREDS)).json()

    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_access_token_rejected_for_refresh(client: AsyncClient) -> None:
    await _register(client)
    tokens = (await client.post("/api/v1/auth/login", json=CREDS)).json()

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert resp.status_code == 401


async def test_me_without_token_is_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_register_rate_limited(client: AsyncClient) -> None:
    for i in range(5):
        await client.post(
            "/api/v1/auth/register",
            json={"email": f"u{i}@example.com", "password": "a-long-passphrase"},
        )
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "u6@example.com", "password": "a-long-passphrase"},
    )

    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limited"


async def test_weak_password_rejected_by_validation(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register", json={"email": "x@example.com", "password": "short"}
    )
    assert resp.status_code == 422  # pydantic min_length


async def test_readiness_includes_database(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health/ready")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] is True
