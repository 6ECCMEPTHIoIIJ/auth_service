from dataclasses import dataclass
from typing import Self

from fastapi import Depends, Request, Response

from app.modules.auth.dtos.signin import SigninRequestBody, SigninResponse

from .signin import SigninService


@dataclass(slots=True)
class SigninController:
    _signin: SigninService

    async def signin(
        self, request_body: SigninRequestBody, request: Request, response: Response
    ) -> SigninResponse:
        result = await self._signin(request_body, request, response)
        return SigninResponse(id=str(result.id), name=result.name)

    @classmethod
    def provider(
        cls,
        signin_service: SigninService = Depends(SigninService.provider),  # noqa: B008
    ) -> Self:
        return cls(_signin=signin_service)
