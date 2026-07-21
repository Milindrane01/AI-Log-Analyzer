"""Auth endpoints — thin: validate wire format, call service, shape response."""

from fastapi import APIRouter, Depends, status

from app.api.deps import DBDep, SettingsDep
from app.core.ratelimit import RateLimiter
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    summary="Create an account",
)
async def register(body: RegisterRequest, session: DBDep, settings: SettingsDep) -> UserResponse:
    user = await AuthService(session, settings).register(body.email, body.password)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    summary="Exchange credentials for a token pair",
)
async def login(body: LoginRequest, session: DBDep, settings: SettingsDep) -> TokenResponse:
    pair = await AuthService(session, settings).login(body.email, body.password)
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh", response_model=TokenResponse, summary="Rotate a refresh token")
async def refresh(body: RefreshRequest, session: DBDep, settings: SettingsDep) -> TokenResponse:
    pair = await AuthService(session, settings).refresh(body.refresh_token)
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)
