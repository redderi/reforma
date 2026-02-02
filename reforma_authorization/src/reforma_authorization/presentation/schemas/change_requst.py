from pydantic import BaseModel, EmailStr

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr

class ChangeUsernameRequest(BaseModel):
    new_username: str