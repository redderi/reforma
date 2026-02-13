from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class RefreshToken:
    token: str
    user_id: uuid.UUID
    device_id: str
    expires_at: datetime