"""Схема хранения пользователя (PostgreSQL).

Таблица ``users`` — учётные записи для signup/signin.

+------------------+------------------+------------------------------------------+
| Поле             | Тип              | Назначение                               |
+==================+==================+==========================================+
| ``id``           | UUID (PK)        | Стабильный идентификатор пользователя    |
+------------------+------------------+------------------------------------------+
| ``name``         | строка, unique   | Имя / логин (уникальное при регистрации) |
+------------------+------------------+------------------------------------------+
| ``password_hash``| строка           | Хеш пароля (argon2), не plaintext        |
+------------------+------------------+------------------------------------------+
| ``created_at``   | timestamptz      | Наследуется от ``orm.Base``              |
+------------------+------------------+------------------------------------------+
| ``updated_at``   | timestamptz      | Наследуется от ``orm.Base``              |
+------------------+------------------+------------------------------------------+

Пароль в БД не хранится — только результат ``PasswordHasher.hash()`` (argon2).
"""

import uuid

from orm import Base
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
