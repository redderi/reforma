from dataclasses import dataclass, field
from uuid import UUID
from typing import List

@dataclass
class UserProfile:
    id: UUID
    username: str
    email: str
    profile_picture: str | None = None
    bio: str | None = None
    surveys: List[UUID] = field(default_factory=list)   # ID созданных опросов
    templates: List[UUID] = field(default_factory=list) # ID шаблонов
    reports: List[UUID] = field(default_factory=list)   # ID отчетов по опросам