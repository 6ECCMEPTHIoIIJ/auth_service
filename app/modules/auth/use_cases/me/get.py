from typing import Self
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from pipeline import Pipeline, PipelineBuilder, PipelineCtx

from app.services.cookies import CookiesService
from app.services.jwt import AccessClaims, JwtService


@dataclass(slots=True, frozen=True)
class GetMeResult:
    id: uuid.UUID


@dataclass(slots=True)
class GetMePipelineCtx(PipelineCtx):
    request: Request

    access_token: str | None = None
    claims: AccessClaims | None = None
    user_id: uuid.UUID | None = None


def get_access_token(
    cookies_service: CookiesService,
) -> Callable[[GetMePipelineCtx], None]:
    def _get_access_token(ctx: GetMePipelineCtx) -> None:
        ctx.access_token = cookies_service.get_access_cookie(ctx.request)
        if not ctx.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No access token"
            )

    return _get_access_token


def verify_access_token(jwt_service: JwtService) -> Callable[[GetMePipelineCtx], None]:
    def _verify_access_token(ctx: GetMePipelineCtx) -> None:
        try:
            ctx.claims = jwt_service.verify_access(ctx.access_token)
        except Exception as exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad access token"
            ) from exception

    return _verify_access_token


def get_user_id(ctx: GetMePipelineCtx) -> None:
    ctx.user_id = uuid.UUID(ctx.claims.sub)


class GetMeService:
    _pipeline: Pipeline

    def __init__(
        self, *, cookies_service: CookiesService, jwt_service: JwtService
    ) -> None:
        self._pipeline = PipelineBuilder.pipe(
            lambda b: b.do(get_access_token(cookies_service)),
            lambda b: b.do(verify_access_token(jwt_service)),
            lambda b: b.do(get_user_id),
        ).build()

    def __call__(self, request: Request) -> GetMeResult:
        ctx = GetMePipelineCtx(request=request)
        self._pipeline(ctx)

        return GetMeResult(id=ctx.user_id)

    @classmethod
    def provider(
        cls,
        cookies_service: CookiesService = Depends(CookiesService.from_settings),  # noqa: B008
        jwt_service: JwtService = Depends(JwtService.from_request),  # noqa: B008
    ) -> Self:
        return cls(cookies_service=cookies_service, jwt_service=jwt_service)
