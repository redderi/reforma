from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_id: str

class PromoteRequest(BaseModel):
    new_role: str

class SuspendRequest(BaseModel):
    reason: str

class RestoreRequest(BaseModel):
    email: EmailStr