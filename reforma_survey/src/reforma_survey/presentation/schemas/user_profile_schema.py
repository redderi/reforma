from typing import List, Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field


class UserProfileOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    profile_picture: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None  
    country: Optional[str] = None
    city: Optional[str] = None
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
        description="Имя пользователя от 3 до 50 символов"
    )


class EmailUpdate(BaseModel):
    email: EmailStr


class ProfilePictureUpdate(BaseModel):
    picture_url: Optional[str] = None


class BioUpdate(BaseModel):
    bio: Optional[str] = None


class GenderUpdate(BaseModel):
    gender: Optional[str] = Field(
        None,
        description="Пол: male, female, other, prefer_not_to_say"
    )


class BirthDateUpdate(BaseModel):
    birth_date: Optional[date] = None


class LocationUpdate(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
