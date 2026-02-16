from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from reforma_common.user_status import UserStatus

@dataclass
class User:
    id: UUID
    username: str
    email: str
    role: str
    password_hash: str
    is_email_verified: bool = False

    status: UserStatus = UserStatus.REGISTERED
    is_email_verified: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None

    suspended_at: datetime | None = None
    suspension_reason: str | None = None
    suspended_by: UUID | None = None