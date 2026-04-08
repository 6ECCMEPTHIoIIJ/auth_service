import hmac
import secrets
from typing import Self

from fastapi import HTTPException, Request, status

from app.config import settings

CSRF_HEADER = "X-CSRF-Token"


class CsrfService:
    def __init__(self, *, cookie_name: str) -> None:
        self._cookie_name = cookie_name

    def generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def require_double_submit(self, request: Request) -> None:
        cookie_token = request.cookies.get(self._cookie_name)
        header_token = request.headers.get(CSRF_HEADER)

        if not cookie_token or not header_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF required"
            )
        if not hmac.compare_digest(cookie_token, header_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Bad CSRF token"
            )

    @classmethod
    def from_settings(cls) -> Self:
        return cls(cookie_name=settings.csrf_cookie_name)
