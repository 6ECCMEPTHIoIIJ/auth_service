# ruff: noqa: B008

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import User
from app.db.session import get_db_session
from app.pipeline import (
    AuthPipelineCtx,
    LoginInput,
    build_login_pipeline,
    build_logout_pipeline,
    build_refresh_pipeline,
)
from app.services import cookies, csrf, passwords
from app.services.jwt import JwtService
from app.services.redis_refresh import RefreshStore

router = APIRouter(prefix="/auth", tags=["auth"])


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_jwt(request: Request) -> JwtService:
    return request.app.state.jwt


def get_refresh_store(request: Request) -> RefreshStore:
    return request.app.state.refresh_store


class SignupBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6, max_length=1024)


class LoginBody(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(
    body: LoginBody,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    jwt_svc: JwtService = Depends(get_jwt),
    refresh_store: RefreshStore = Depends(get_refresh_store),
) -> None:
    pipeline = build_login_pipeline(
        data=LoginInput(name=body.name, password=body.password)
    )
    ctx = AuthPipelineCtx(
        request=request,
        response=response,
        db=db,
        redis=redis,
        jwt=jwt_svc,
        refresh_store=refresh_store,
    )
    await pipeline(ctx)


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    jwt_svc: JwtService = Depends(get_jwt),
    refresh_store: RefreshStore = Depends(get_refresh_store),
) -> None:
    pipeline = build_refresh_pipeline()
    ctx = AuthPipelineCtx(
        request=request,
        response=response,
        db=db,
        redis=redis,
        jwt=jwt_svc,
        refresh_store=refresh_store,
    )
    await pipeline(ctx)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis),
    jwt_svc: JwtService = Depends(get_jwt),
    refresh_store: RefreshStore = Depends(get_refresh_store),
) -> None:
    pipeline = build_logout_pipeline()
    ctx = AuthPipelineCtx(
        request=request,
        response=response,
        db=db,
        redis=redis,
        jwt=jwt_svc,
        refresh_store=refresh_store,
    )
    await pipeline(ctx)
