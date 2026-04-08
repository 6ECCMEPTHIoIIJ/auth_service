from typing import Self
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, Response, status
from pipeline import PipelineCtx
from pipeline.aio import AsyncPipeline, AsyncPipelineBuilder

from app.modules.auth.db.user import UserRepo
from app.modules.auth.domain.user import UserAccount
from app.modules.auth.dtos.signin import SigninRequestBody
from app.services.cookies import CookiesService
from app.services.csrf import CsrfService
from app.services.jwt import JwtService
from app.services.passwords import PasswordService
from app.services.redis_refresh import RefreshStore


@dataclass(slots=True, frozen=True)
class SigninResult:
    id: uuid.UUID
    name: str


@dataclass(slots=True)
class SigninPipelineCtx(PipelineCtx):
    request_body: SigninRequestBody
    request: Request
    response: Response

    user_account: UserAccount | None = None
    access_token: str | None = None
    refresh_id: str | None = None
    csrf_token: str | None = None


async def validate_csrf_token(
    csrf_service: CsrfService,
) -> Callable[[SigninPipelineCtx], None]:
    async def _validate_csrf_token(ctx: SigninPipelineCtx) -> None:
        csrf_service.require_double_submit(ctx.request)

    return _validate_csrf_token


async def load_user_account(
    user_repo: UserRepo,
) -> Callable[[SigninPipelineCtx], None]:
    async def _load_user_account(ctx: SigninPipelineCtx) -> None:
        ctx.user_account = await user_repo.get_by_name(ctx.request_body.name)
        if ctx.user_account is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

    return _load_user_account


async def verify_password(
    password_service: PasswordService,
) -> Callable[[SigninPipelineCtx], None]:
    async def _verify_password(ctx: SigninPipelineCtx) -> None:
        if not password_service.verify_password(
            ctx.user_account.password_hash, ctx.request_body.password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

    return _verify_password


async def issue_tokens(
    jwt_service: JwtService,
    refresh_store: RefreshStore,
) -> Callable[[SigninPipelineCtx], None]:
    async def _issue_tokens(ctx: SigninPipelineCtx) -> None:
        ctx.access_token = jwt_service.issue_access(ctx.user_account.id)
        ctx.refresh_id = await refresh_store.create(ctx.user_account.id)

    return _issue_tokens


async def ensure_csrf_token(
    csrf_service: CsrfService,
) -> Callable[[SigninPipelineCtx], None]:
    async def _ensure_csrf_token(ctx: SigninPipelineCtx) -> None:
        ctx.csrf_token = csrf_service.generate_token()

    return _ensure_csrf_token


async def set_cookies(
    cookies_service: CookiesService,
) -> Callable[[SigninPipelineCtx], None]:
    async def _set_cookies(ctx: SigninPipelineCtx) -> None:
        cookies_service.set_csrf_cookie(ctx.response, csrf_token=ctx.csrf_token)
        cookies_service.set_access_cookie(ctx.response, token=ctx.access_token)
        cookies_service.set_refresh_cookie(ctx.response, refresh_id=ctx.refresh_id)

    return _set_cookies


@dataclass(slots=True)
class SigninService:
    _pipeline: AsyncPipeline

    def __init__(
        self,
        *,
        csrf_service: CsrfService,
        user_repo: UserRepo,
        password_service: PasswordService,
        jwt_service: JwtService,
        refresh_store: RefreshStore,
        cookies_service: CookiesService,
    ) -> None:
        self._pipeline = AsyncPipelineBuilder.pipe(
            lambda b: b.do(validate_csrf_token(csrf_service=csrf_service)),
            lambda b: b.do(load_user_account(user_repo=user_repo)),
            lambda b: b.do(verify_password(password_service=password_service)),
            lambda b: b.do(
                issue_tokens(jwt_service=jwt_service, refresh_store=refresh_store)
            ),
            lambda b: b.do(ensure_csrf_token(csrf_service=csrf_service)),
            lambda b: b.do(set_cookies(cookies_service=cookies_service)),
        ).build()

    async def __call__(
        self,
        request_body: SigninRequestBody,
        request: Request,
        response: Response,
    ) -> SigninResult:
        ctx = SigninPipelineCtx(
            request_body=request_body, request=request, response=response
        )
        await self._pipeline(ctx)

        return SigninResult(id=ctx.user_account.id, name=ctx.user_account.name)

    @classmethod
    def provider(
        cls,
        csrf_service: CsrfService = Depends(CsrfService.from_settings),  # noqa: B008
        user_repo: UserRepo = Depends(UserRepo.provider),  # noqa: B008
        password_service: PasswordService = Depends(PasswordService.provider),  # noqa: B008
        jwt_service: JwtService = Depends(JwtService.from_request),  # noqa: B008
        refresh_store: RefreshStore = Depends(RefreshStore.from_request),  # noqa: B008
        cookies_service: CookiesService = Depends(CookiesService.from_settings),  # noqa: B008
    ) -> Self:
        return cls(
            csrf_service=csrf_service,
            user_repo=user_repo,
            password_service=password_service,
            jwt_service=jwt_service,
            refresh_store=refresh_store,
            cookies_service=cookies_service,
        )
