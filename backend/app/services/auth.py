"""Authentication use-cases: register, login, refresh.

Note what is NOT here: no Request, no Response, no status codes. The service
speaks domain language (users, tokens, DomainErrors); HTTP is the router's job.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    TokenError,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.audit import AuditRepository
from app.repositories.user import UserRepository

log = structlog.get_logger()


class TokenPair:
    def __init__(self, access_token: str, refresh_token: str) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._users = UserRepository(session)
        self._audit = AuditRepository(session)
        self._settings = settings

    async def register(self, email: str, password: str) -> User:
        if await self._users.get_by_email(email) is not None:
            await self._audit.record("user.register", "failure", context={"email": email})
            raise ConflictError("An account with this email already exists")
        user = await self._users.create(email=email, hashed_password=hash_password(password))
        await self._audit.record("user.register", "success", user_id=user.id)
        log.info("user_registered", user_id=user.id)
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        # Same error for "no such user" and "wrong password": never reveal
        # which emails have accounts (user enumeration defense).
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.hashed_password)
        ):
            await self._audit.record("user.login", "failure", context={"email": email})
            raise AuthenticationError("Invalid email or password")
        await self._audit.record("user.login", "success", user_id=user.id)
        return self._issue_pair(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(self._settings, refresh_token, expected_type="refresh")
        except TokenError as exc:
            await self._audit.record("token.refresh", "failure", context={"reason": str(exc)})
            raise AuthenticationError("Invalid or expired refresh token") from exc
        user = await self._users.get_by_id(payload["sub"])
        if user is None or not user.is_active:
            raise AuthenticationError("Account no longer active")
        await self._audit.record("token.refresh", "success", user_id=user.id)
        # Rotation: a fresh PAIR every time. Server-side jti denylist lands in
        # M3 (needs Redis) to make rotation airtight against replay.
        return self._issue_pair(user.id)

    def _issue_pair(self, user_id: str) -> TokenPair:
        return TokenPair(
            access_token=create_token(self._settings, user_id, "access"),
            refresh_token=create_token(self._settings, user_id, "refresh"),
        )
