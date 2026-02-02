from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    is_email_verified: bool = False