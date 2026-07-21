"""FastAPI dependency-injection wiring.

Routers declare WHAT they need via type aliases; this module decides HOW it's
provided. Tests swap implementations via app.dependency_overrides.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import TokenError, decode_token
from app.models.user import User
from app.repositories.user import UserRepository

SettingsDep = Annotated[Settings, Depends(get_settings)]
DBDep = Annotated[AsyncSession, Depends(get_db)]

# auto_error=False: missing header becomes OUR 401 JSON shape, not FastAPI's default 403.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    settings: SettingsDep,
    session: DBDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Resolve the Bearer token to an active User, or raise 401."""
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    try:
        payload = decode_token(settings, credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise AuthenticationError("Invalid or expired token") from exc
    user = await UserRepository(session).get_by_id(payload["sub"])
    if user is None or not user.is_active:
        raise AuthenticationError("Account no longer active")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
