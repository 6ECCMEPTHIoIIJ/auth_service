from __future__ import annotations

from dataclasses import dataclass

from backend_core.src.pipeline.aio import AsyncPipelineBuilder
from fastapi import HTTPException, status
from sqlalchemy import select

from app.config import settings
from app.db.models import User
from app.pipeline.ctx import AuthPipelineCtx
from app.services import cookies, csrf, passwords


@dataclass(frozen=True, slots=True)
class LoginInput:
    name: str
    password: str


async def _load_user(ctx: AuthPipelineCtx) -> User:
    result = await ctx.db.execute(select(User).where(User.name == ctx.user_name))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials"
        )
    return user


def build_login_pipeline(*, data: LoginInput):
    async def validate_csrf(ctx: AuthPipelineCtx):
        csrf.require_csrf_double_submit(
            ctx.request, cookie_name=settings.csrf_cookie_name
        )

    async def set_input(ctx: AuthPipelineCtx):
        ctx.user_name = data.name

    async def verify_password_step(ctx: AuthPipelineCtx):
        user = await _load_user(ctx)
        if not passwords.verify_password(user.password_hash, data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials"
            )
        ctx.user_id = str(user.id)

    async def issue_tokens(ctx: AuthPipelineCtx):
        ctx.access_token = ctx.jwt.issue_access(user_id=ctx.user_id)
        ctx.refresh_id = await ctx.refresh_store.create(
            user_id=ctx.user_id, ttl_seconds=settings.refresh_token_ttl_seconds
        )

    async def ensure_csrf_cookie(ctx: AuthPipelineCtx):
        # For clients: refresh/logout require X-CSRF-Token that matches this cookie.
        # Keep the same token if already set.
        token = (
            ctx.request.cookies.get(settings.csrf_cookie_name) or csrf.new_csrf_token()
        )
        ctx.csrf_token = token

    async def set_cookies(ctx: AuthPipelineCtx):
        cookies.set_access_cookie(ctx.response, token=ctx.access_token)
        cookies.set_refresh_cookie(ctx.response, refresh_id=ctx.refresh_id)
        cookies.set_csrf_cookie(ctx.response, csrf_token=ctx.csrf_token)

    return (
        AsyncPipelineBuilder()
        .do(set_input)
        .do(validate_csrf)
        .do(verify_password_step)
        .do(issue_tokens)
        .do(ensure_csrf_cookie)
        .do(set_cookies)
        .build()
    )
