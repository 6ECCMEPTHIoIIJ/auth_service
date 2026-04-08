from typing import Self
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from pipeline import PipelineCtx
from pipeline.aio import AsyncPipeline, AsyncPipelineBuilder

from app.modules.auth.db.user import UserRepo
from app.modules.auth.domain.user import UserAccount
from app.modules.auth.dtos import SignupRequestBody
from app.services.passwords import PasswordService


@dataclass(slots=True, frozen=True)
class SignupResult:
    id: uuid.UUID
    name: str


@dataclass(slots=True)
class SignupPipelineCtx(PipelineCtx):
    request_body: SignupRequestBody

    user_account: UserAccount | None = None


def create_user(
    *,
    password_service: PasswordService,
) -> Callable[[SignupPipelineCtx], None]:
    def _create_user(ctx: SignupPipelineCtx) -> None:
        ctx.user_account = UserAccount(
            name=ctx.request_body.name,
            password_hash=password_service.hash(ctx.request_body.password),
        )

    return _create_user


def save_user(
    *,
    user_repo: UserRepo,
) -> Callable[[SignupPipelineCtx], Awaitable[None]]:
    async def _save_user(
        ctx: SignupPipelineCtx,
    ) -> Callable[[SignupPipelineCtx], Awaitable[None]]:
        ctx.user_account = await user_repo.create(ctx.user_account)

        async def _rollback(ctx: SignupPipelineCtx) -> None:
            await user_repo.delete(ctx.user_account.id)

        return _rollback

    return _save_user


def validate_user_name(
    *,
    user_repo: UserRepo,
) -> Callable[[SignupPipelineCtx], Awaitable[None]]:
    async def _validate_user_name(ctx: SignupPipelineCtx) -> None:
        if await user_repo.get_by_name(ctx.user_account.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User name is already taken",
            )

    return _validate_user_name


@dataclass(slots=True)
class SignupService:
    _pipeline: AsyncPipeline

    def __init__(
        self, *, password_service: PasswordService, user_repo: UserRepo
    ) -> None:
        self._pipeline = AsyncPipelineBuilder.pipe(
            lambda b: b.do(validate_user_name(user_repo=user_repo)),
            lambda b: b.do(create_user(password_service=password_service)),
            lambda b: b.do(save_user(user_repo=user_repo)),
        ).build()

    async def __call__(self, request_body: SignupRequestBody) -> SignupResult:
        ctx = SignupPipelineCtx(request_body=request_body)
        await self._pipeline(ctx)

        return SignupResult(
            id=ctx.user_account.id,
            name=ctx.user_account.name,
        )

    @classmethod
    def provider(
        cls,
        password_service: PasswordService = Depends(PasswordService.provider),  # noqa: B008
        user_repo: UserRepo = Depends(UserRepo.provider),  # noqa: B008
    ) -> Self:
        return cls(password_service=password_service, user_repo=user_repo)
