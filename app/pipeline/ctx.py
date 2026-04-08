from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request, Response
from pipeline import PipelineCtx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.jwt import JwtService
from app.services.redis_refresh import RefreshStore


@dataclass(kw_only=True, slots=True)
class AuthPipelineCtx(PipelineCtx):
    request: Request
    response: Response
    db: AsyncSession | None = None
    redis: Redis | None = None
    jwt: JwtService
    refresh_store: RefreshStore

    user_id: str | None = None
    user_name: str | None = None
    access_token: str | None = None
    refresh_id: str | None = None
    csrf_token: str | None = None
