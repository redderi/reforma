from dataclasses import dataclass
from datetime import datetime

@dataclass
class RefreshToken:
    token: str
    user_id: int
    device_id: str
    expires_at: datetime