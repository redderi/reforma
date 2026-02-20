from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class EmailVerificationToken:
    token: str
    user_id: UUID
    expires_at: datetime
    data: dict | None = None
