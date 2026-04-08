from dataclasses import dataclass
from typing import Self

from fastapi.params import Depends

from app.modules.auth.dtos import SignupRequestBody, SignupResponse

from .signup import SignupService


@dataclass(slots=True)
class SignupController:
    _signup: SignupService

    async def signup(self, request_body: SignupRequestBody) -> SignupResponse:
        result = await self._signup(request_body)
        return SignupResponse(id=str(result.id), name=result.name)

    @classmethod
    def provider(
        cls,
        signup_service: SignupService = Depends(SignupService.provider),  # noqa: B008
    ) -> Self:
        return cls(_signup=signup_service)
