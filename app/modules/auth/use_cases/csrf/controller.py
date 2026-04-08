from dataclasses import dataclass
from typing import Self

from fastapi import Depends, Response

from .issue import IssueCsrfTokenService


@dataclass(slots=True)
class CsrfTokenController:
    _issue: IssueCsrfTokenService

    def issue(self, response: Response) -> None:
        self._issue(response)

    @classmethod
    def provider(
        cls,
        issue_csrf_token_service: IssueCsrfTokenService = Depends(  # noqa: B008
            IssueCsrfTokenService.provider
        ),
    ) -> Self:
        return cls(_issue=issue_csrf_token_service)
