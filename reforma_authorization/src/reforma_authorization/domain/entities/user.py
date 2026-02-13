from dataclasses import dataclass
import uuid

@dataclass
class User:
    id: uuid.UUID
    username: str
    email: str
    password_hash: str
    is_email_verified: bool = False