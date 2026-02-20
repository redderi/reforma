from dataclasses import dataclass, field
from uuid import UUID
from typing import List
from datetime import date


@dataclass
class UserProfile:
    id: UUID
    username: str
    email: str

    profile_picture: str | None = None
    bio: str | None = None

    gender: str | None = None
    birth_date: date | None = None
    country: str | None = None
    city: str | None = None

    balance: int = 0

    surveys: List[UUID] = field(default_factory=list)
    templates: List[UUID] = field(default_factory=list)
    reports: List[UUID] = field(default_factory=list)
    responses: List[UUID] = field(default_factory=list)
