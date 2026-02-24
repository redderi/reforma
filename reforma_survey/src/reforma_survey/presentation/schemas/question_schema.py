from typing import Dict, List

from pydantic import BaseModel, Field


class QuestionOut(BaseModel):
    id: str
    survey_id: str
    text: str
    type: str
    options: List[str] = []
    style: Dict = {}
    order: int = 0


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    type: str = Field(
        ..., description="single_choice, multiple_choice, text, slider, rating и т.д."
    )
    options: List[str] | None = None
    style: Dict | None = None


class QuestionTextUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class QuestionTypeUpdate(BaseModel):
    type: str


class QuestionOptionsUpdate(BaseModel):
    options: List[str]


class QuestionStyleUpdate(BaseModel):
    style: Dict


class QuestionOrderUpdate(BaseModel):
    order: int = Field(ge=0)
