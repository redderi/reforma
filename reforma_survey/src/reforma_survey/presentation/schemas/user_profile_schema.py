from typing import List
from datetime import date
from pydantic import BaseModel, EmailStr, Field


class UserProfileOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    profile_picture: str | None = None
    bio: str | None = None
    gender: str | None = None
    birth_date: str | None = None
    country: str | None = None
    city: str | None = None
    balance: int = 0
    surveys: List[str] = []
    templates: List[str] = []
    reports: List[str] = []

    class Config:
        from_attributes = True


class UsernameUpdate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        strip_whitespace=True,
        description="Имя пользователя от 3 до 50 символов",
    )


class EmailUpdate(BaseModel):
    email: EmailStr


class ProfilePictureUpdate(BaseModel):
    picture_url: str | None = None


class BioUpdate(BaseModel):
    bio: str | None = None


class GenderUpdate(BaseModel):
    gender: str | None = Field(
        None, description="Пол: male, female, other, prefer_not_to_say"
    )


class BirthDateUpdate(BaseModel):
    birth_date: date | None = None


class LocationUpdate(BaseModel):
    country: str | None = None
    city: str | None = None
