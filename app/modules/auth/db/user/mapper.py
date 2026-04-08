from typing import Self

from app.modules.auth.db.user import UserModel
from app.modules.auth.domain.user import UserAccount


class UserMapper:
    def to_domain(self, user: UserModel) -> UserAccount:
        return UserAccount(
            id=user.id,
            name=user.name,
            password_hash=user.password_hash,
        )

    def from_domain(self, user: UserAccount) -> UserModel:
        return UserModel(
            **({"id": user.id} if user.id is not None else {}),
            name=user.name,
            password_hash=user.password_hash,
        )

    @classmethod
    def provider(cls) -> Self:
        return cls()
