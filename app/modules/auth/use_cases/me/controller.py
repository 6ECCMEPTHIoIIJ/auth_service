from dataclasses import dataclass
from typing import Self

from fastapi import Depends, Request

from app.modules.auth.dtos import GetMeResponse

from .get import GetMeService


@dataclass(slots=True)
class MeController:
    _get: GetMeService

    def get(
        self,
        request: Request,
    ) -> GetMeResponse:
        result = self._get(request)
        return GetMeResponse(id=str(result.id))

    @classmethod
    def provider(
        cls,
        get_me_service: GetMeService = Depends(GetMeService.provider),  # noqa: B008
    ) -> Self:
        return cls(_get=get_me_service)
