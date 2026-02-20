from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class RefreshToken:
    token: str
    jti: str
    user_id: UUID
    device_id: str
    expires_at: datetime
    revoked: bool = False
