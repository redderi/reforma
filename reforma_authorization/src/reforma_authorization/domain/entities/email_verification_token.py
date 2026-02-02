from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmailVerificationToken:
    token: str
    user_id: int
    expires_at: datetime