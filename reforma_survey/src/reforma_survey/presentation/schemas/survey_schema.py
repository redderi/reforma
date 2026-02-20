from uuid import UUID
from typing import Dict, List
from pydantic import BaseModel, Field


class SurveyOut(BaseModel):
    id: str
    owner_id: str
    title: str
    description: str | None = None
    published: bool = False
    questions: List[str] = []
    settings: Dict = {}
    template_id: str | None  = None


class SurveyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None  = None
    settings: Dict | None  = None
    template_id: UUID | None  = None


class SurveyTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class SurveyDescriptionUpdate(BaseModel):
    description: str | None  = None


class SurveySettingsUpdate(BaseModel):
    settings: Dict


class SurveyTemplateUpdate(BaseModel):
    template_id: UUID | None  = None


class AddQuestionRequest(BaseModel):
    question_id: UUID


class ReorderQuestionsRequest(BaseModel):
    question_ids: List[UUID]
