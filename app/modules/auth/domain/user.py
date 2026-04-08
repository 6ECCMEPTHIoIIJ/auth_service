import uuid
from dataclasses import dataclass


@dataclass(slots=True)
class UserAccount:
    id: uuid.UUID | None = None
    name: str
    password_hash: str
