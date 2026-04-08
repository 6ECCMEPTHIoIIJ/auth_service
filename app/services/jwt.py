import time
from dataclasses import dataclass
from typing import Any, Self

import jwt
from fastapi import Request


@dataclass(frozen=True, slots=True)
class AccessClaims:
    sub: str
    iat: int
    exp: int


class JwtService:
    def __init__(self, *, secret: str, algorithm: str, access_ttl_seconds: int):
        self._secret = secret
        self._algorithm = algorithm
        self._access_ttl_seconds = int(access_ttl_seconds)

    def issue_access(self, *, user_id: str) -> str:
        now = int(time.time())
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + self._access_ttl_seconds,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_access(self, token: str) -> AccessClaims:
        payload: dict[str, Any] = jwt.decode(
            token,
            self._secret,
            algorithms=[self._algorithm],
            options={"require": ["sub", "iat", "exp"]},
        )
        return AccessClaims(
            sub=str(payload["sub"]),
            iat=int(payload["iat"]),
            exp=int(payload["exp"]),
        )

    @classmethod
    def from_request(cls, request: Request) -> Self:
        return request.app.state.jwt
