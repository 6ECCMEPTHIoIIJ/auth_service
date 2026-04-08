from __future__ import annotations

from backend_core.src.pipeline.aio import AsyncPipelineBuilder
from fastapi import status

from app.config import settings
from app.pipeline.ctx import AuthPipelineCtx
from app.services import cookies, csrf


def build_logout_pipeline():
    async def validate_csrf(ctx: AuthPipelineCtx):
        csrf.require_csrf_double_submit(ctx.request, cookie_name=settings.csrf_cookie_name)

    async def revoke_refresh(ctx: AuthPipelineCtx):
        refresh_id = ctx.request.cookies.get(settings.refresh_cookie_name)
        if refresh_id:
            await ctx.refresh_store.revoke(refresh_id)

    async def clear(ctx: AuthPipelineCtx):
        cookies.clear_auth_cookies(ctx.response)

    return AsyncPipelineBuilder().do(validate_csrf).do(revoke_refresh).do(clear).build()

