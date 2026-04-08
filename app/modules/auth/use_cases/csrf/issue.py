from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from fastapi import Depends, Response
from pipeline import Pipeline, PipelineBuilder, PipelineCtx

from app.services.cookies import CookiesService
from app.services.csrf import CsrfService


@dataclass(slots=True)
class IssueCsrfTokenPipelineCtx(PipelineCtx):
    response: Response
    csrf_token: str | None = None


def create_csrf_token(
    csrf_service: CsrfService,
) -> Callable[[IssueCsrfTokenPipelineCtx], None]:
    def _create_csrf_token(ctx: IssueCsrfTokenPipelineCtx) -> None:
        ctx.csrf_token = csrf_service.generate_token()

    return _create_csrf_token


def set_csrf_cookie(
    cookies_service: CookiesService,
) -> Callable[[IssueCsrfTokenPipelineCtx], None]:
    def _set_csrf_cookie(ctx: IssueCsrfTokenPipelineCtx) -> None:
        cookies_service.set_csrf_cookie(ctx.response, csrf_token=ctx.csrf_token)

    return _set_csrf_cookie


@dataclass(slots=True)
class IssueCsrfTokenService:
    _pipeline: Pipeline

    def __init__(
        self, *, csrf_service: CsrfService, cookies_service: CookiesService
    ) -> None:
        self._pipeline = PipelineBuilder.pipe(
            lambda b: b.do(create_csrf_token(csrf_service)),
            lambda b: b.do(set_csrf_cookie(cookies_service)),
        ).build()

    def __call__(self, response: Response) -> None:
        ctx = IssueCsrfTokenPipelineCtx(response=response)
        self._pipeline(ctx)

    @classmethod
    def provider(
        cls,
        csrf_service: CsrfService = Depends(CsrfService.from_settings),  # noqa: B008
        cookies_service: CookiesService = Depends(CookiesService.from_settings),  # noqa: B008
    ) -> Self:
        return cls(csrf_service=csrf_service, cookies_service=cookies_service)
