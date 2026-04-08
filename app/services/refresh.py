from __future__ import annotations

from backend_core.src.pipeline.aio import AsyncPipelineBuilder
from fastapi import HTTPException, status

from app.config import settings
from app.pipeline.ctx import AuthPipelineCtx
from app.services import cookies, csrf


def build_refresh_pipeline():
    async def validate_csrf(ctx: AuthPipelineCtx):
        csrf.require_csrf_double_submit(
            ctx.request, cookie_name=settings.csrf_cookie_name
        )

    async def read_refresh_cookie(ctx: AuthPipelineCtx):
        refresh_id = ctx.request.cookies.get(settings.refresh_cookie_name)
        if not refresh_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token"
            )
        ctx.refresh_id = refresh_id

    async def rotate_refresh(ctx: AuthPipelineCtx):
        new_id = await ctx.refresh_store.rotate(
            refresh_id=ctx.refresh_id, ttl_seconds=settings.refresh_token_ttl_seconds
        )
        if new_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )
        ctx.refresh_id = new_id

    async def issue_access(ctx: AuthPipelineCtx):
        session = await ctx.refresh_store.get(ctx.refresh_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )
        ctx.user_id = session.user_id
        ctx.access_token = ctx.jwt.issue_access(user_id=ctx.user_id)

    async def set_cookies(ctx: AuthPipelineCtx):
        cookies.set_access_cookie(ctx.response, token=ctx.access_token)
        cookies.set_refresh_cookie(ctx.response, refresh_id=ctx.refresh_id)

    return (
        AsyncPipelineBuilder()
        .do(validate_csrf)
        .do(read_refresh_cookie)
        .do(rotate_refresh)
        .do(issue_access)
        .do(set_cookies)
        .build()
    )

class RefreshService:
    