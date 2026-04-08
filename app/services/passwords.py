from dataclasses import dataclass, field
from typing import Self

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


@dataclass(slots=True)
class PasswordService:
    _hasher: PasswordHasher = field(default_factory=PasswordHasher, init=False)

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False

    @classmethod
    def provider(cls) -> Self:
        return cls()
