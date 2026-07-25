"""Password hashing (bcrypt) and JWT creation/verification.

bcrypt directly, not passlib: passlib is unmaintained and breaks with bcrypt>=4.1.
bcrypt is slow BY DESIGN (work factor) — that slowness is the brute-force defense.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import Settings

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised for any invalid token: expired, tampered, wrong type."""


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    # bcrypt.checkpw is constant-time — immune to timing attacks.
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(settings: Settings, user_id: str, token_type: TokenType) -> str:
    """Create a signed JWT.

    Claims: sub (user id), type (access|refresh — so a refresh token can never
    be used as an access token), jti (unique id, enables future revocation
    lists), iat/exp (validity window).
    """
    if token_type == "access":  # noqa: S105 -- type tag, not a secret
        lifetime = timedelta(minutes=settings.access_token_expire_minutes)
    else:
        lifetime = timedelta(days=settings.refresh_token_expire_days)

    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(settings: Settings, token: str, expected_type: TokenType) -> dict[str, Any]:
    """Verify signature + expiry + type. Any failure → TokenError (one catch site)."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:  # expired, bad signature, malformed …
        raise TokenError(str(exc)) from exc
    if payload.get("type") != expected_type:
        raise TokenError(f"expected {expected_type} token")
    if "sub" not in payload:
        raise TokenError("missing subject claim")
    return payload
