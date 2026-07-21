"""Aggregates all v1 routers. main.py mounts this once under /api/v1."""

from fastapi import APIRouter

from app.api.v1 import (
    analyses, auth, chat, health, investigations, logs, reports, users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(logs.router)
api_router.include_router(analyses.router)
api_router.include_router(chat.router)
api_router.include_router(reports.router)
api_router.include_router(investigations.router)
