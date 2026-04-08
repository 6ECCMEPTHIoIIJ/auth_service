import secrets
from datetime import UTC, datetime, timedelta
from typing import Self

from fastapi import Request, Response

from app.config import settings


def expires_in(ttl_seconds: int) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=int(ttl_seconds))


class CookiesService:
    def __init__(
        self,
        *,
        access_cookie_name: str,
        refresh_cookie_name: str,
        csrf_cookie_name: str,
        access_token_ttl_seconds: int,
        refresh_token_ttl_seconds: int,
        cookie_secure: bool,
        cookie_samesite: str,
        cookie_domain: str,
    ) -> None:
        self._access_cookie_name = access_cookie_name
        self._refresh_cookie_name = refresh_cookie_name
        self._csrf_cookie_name = csrf_cookie_name
        self._access_token_ttl_seconds = access_token_ttl_seconds
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds
        self._cookie_secure = cookie_secure
        self._cookie_samesite = cookie_samesite
        self._cookie_domain = cookie_domain

    def get_access_cookie(self, request: Request) -> str | None:
        return request.cookies.get(self._access_cookie_name)

    def get_refresh_cookie(self, request: Request) -> str | None:
        return request.cookies.get(self._refresh_cookie_name)

    def get_csrf_cookie(self, request: Request) -> str | None:
        return request.cookies.get(self._csrf_cookie_name)

    def set_access_cookie(self, response: Response, *, token: str) -> None:
        response.set_cookie(
            key=self._access_cookie_name,
            value=token,
            httponly=True,
            secure=self._cookie_secure,
            samesite=self._cookie_samesite,
            domain=self._cookie_domain,
            path="/",
            expires=expires_in(self._access_token_ttl_seconds),
        )

    def set_refresh_cookie(self, response: Response, *, refresh_id: str) -> None:
        response.set_cookie(
            key=self._refresh_cookie_name,
            value=refresh_id,
            httponly=True,
            secure=self._cookie_secure,
            samesite=self._cookie_samesite,
            domain=self._cookie_domain,
            path="/auth/refresh",
            expires=expires_in(self._refresh_token_ttl_seconds),
        )

    def set_csrf_cookie(self, response: Response, *, csrf_token: str) -> None:
        response.set_cookie(
            key=self._csrf_cookie_name,
            value=csrf_token,
            httponly=False,
            secure=self._cookie_secure,
            samesite=self._cookie_samesite,
            domain=self._cookie_domain,
            path="/",
            expires=expires_in(self._refresh_token_ttl_seconds),
        )

    def clear_auth_cookies(self, response: Response) -> None:
        response.delete_cookie(
            key=self._access_cookie_name,
            domain=self._cookie_domain,
            path="/",
        )
        response.delete_cookie(
            key=self._refresh_cookie_name,
            domain=self._cookie_domain,
            path="/auth/refresh",
        )
        response.delete_cookie(
            key=self._csrf_cookie_name,
            domain=self._cookie_domain,
            path="/",
        )

    @classmethod
    def from_settings(cls) -> Self:
        return cls(
            access_cookie_name=settings.access_cookie_name,
            refresh_cookie_name=settings.refresh_cookie_name,
            csrf_cookie_name=settings.csrf_cookie_name,
            access_token_ttl_seconds=settings.access_token_ttl_seconds,
            refresh_token_ttl_seconds=settings.refresh_token_ttl_seconds,
        )
