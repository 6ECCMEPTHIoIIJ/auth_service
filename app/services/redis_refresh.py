import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Self

from fastapi import Depends, Request
from redis.asyncio import Redis

from auth_service.app.routes.auth import get_redis


@dataclass(frozen=True, slots=True)
class RefreshSession:
    user_id: str
    issued_at: int
    expires_at: int


def _now() -> int:
    return int(time.time())


def _key(refresh_id: str) -> str:
    return f"auth:refresh:{refresh_id}"


def new_refresh_id() -> str:
    # 256-bit URL-safe token; good entropy even if leaked.
    return secrets.token_urlsafe(32)


def _encode_session(session: RefreshSession) -> str:
    return json.dumps(
        {
            "user_id": session.user_id,
            "issued_at": session.issued_at,
            "expires_at": session.expires_at,
        },
        separators=(",", ":"),
    )


def _decode_session(raw: str) -> RefreshSession:
    data: dict[str, Any] = json.loads(raw)
    return RefreshSession(
        user_id=str(data["user_id"]),
        issued_at=int(data["issued_at"]),
        expires_at=int(data["expires_at"]),
    )


ROTATE_LUA = r"""
-- KEYS[1] = old refresh key
-- KEYS[2] = new refresh key
-- ARGV[1] = new json value
-- ARGV[2] = ttl seconds for new key
-- Returns:
--   0 = old key missing
--   1 = rotated ok

if redis.call("EXISTS", KEYS[1]) == 0 then
  return 0
end

redis.call("SET", KEYS[2], ARGV[1], "EX", ARGV[2])
redis.call("DEL", KEYS[1])
return 1
"""


class RefreshStore:
    def __init__(self, redis: Redis):
        self._redis = redis

    async def create(self, *, user_id: str, ttl_seconds: int) -> str:
        refresh_id = new_refresh_id()
        now = _now()
        session = RefreshSession(
            user_id=user_id,
            issued_at=now,
            expires_at=now + int(ttl_seconds),
        )
        await self._redis.set(
            _key(refresh_id), _encode_session(session), ex=int(ttl_seconds)
        )
        return refresh_id

    async def get(self, refresh_id: str) -> RefreshSession | None:
        raw = await self._redis.get(_key(refresh_id))
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return _decode_session(raw)

    async def revoke(self, refresh_id: str) -> None:
        await self._redis.delete(_key(refresh_id))

    async def rotate(self, *, refresh_id: str, ttl_seconds: int) -> str | None:
        old_key = _key(refresh_id)
        raw = await self._redis.get(old_key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        session = _decode_session(raw)

        new_id = new_refresh_id()
        now = _now()
        new_session = RefreshSession(
            user_id=session.user_id,
            issued_at=now,
            expires_at=now + int(ttl_seconds),
        )

        new_key = _key(new_id)
        rotated = await self._redis.eval(
            ROTATE_LUA,
            numkeys=2,
            keys=[old_key, new_key],
            args=[_encode_session(new_session), str(int(ttl_seconds))],
        )
        return new_id if int(rotated) == 1 else None

    @classmethod
    def from_request(cls, request: Request) -> Self:
        return cls(redis=request.app.state.redis)
