import select
import uuid
from dataclasses import dataclass
from typing import Self

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.db.user import UserModel
from app.modules.auth.domain.user import UserAccount
from auth_service.app.db import get_db_session

from .mapper import UserMapper


@dataclass(slots=True)
class UserRepo:
    mapper: UserMapper
    db: AsyncSession

    async def create(self, user_account: UserAccount) -> UserAccount:
        if user_account.id is not None:
            raise ValueError("User ID must be None")

        user = self.mapper.from_domain(user_account)
        self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)
        return self.mapper.to_domain(user)

    async def get(self, id: uuid.UUID) -> UserAccount | None:
        user = await self.db.get(UserModel, id)
        return self.mapper.to_domain(user) if user else None

    async def get_by_name(self, name: str) -> UserAccount | None:
        user = await self.db.scalar(select(UserModel).where(UserModel.name == name))
        return self.mapper.to_domain(user) if user else None

    async def update(self, user_account: UserAccount) -> UserAccount:
        if user_account.id is None:
            raise ValueError("User ID is required")

        user = await self.db.get(UserModel, user_account.id)
        if user is None:
            raise ValueError("User not found")

        user.name = user_account.name
        user.password_hash = user_account.password_hash

        await self.db.commit()
        await self.db.refresh(user)
        return self.mapper.to_domain(user)

    async def delete(self, id: uuid.UUID) -> bool:
        user = await self.db.get(UserModel, id)
        if user is None:
            return False

        self.db.delete(user)
        await self.db.commit()
        return True

    @classmethod
    def provider(
        cls,
        *,
        db: AsyncSession = Depends(get_db_session),  # noqa: B008
        mapper: UserMapper = Depends(UserMapper.provider),  # noqa: B008
    ) -> Self:
        return cls(mapper=mapper, db=db)
