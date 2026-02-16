from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class EmailVerificationToken:
    token: str
    user_id: uuid.UUID
    expires_at: datetime
    data: dict | None = None 