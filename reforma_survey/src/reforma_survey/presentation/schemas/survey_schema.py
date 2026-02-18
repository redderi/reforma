from uuid import UUID
from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class SurveyOut(BaseModel):
    id: str
    owner_id: str
    title: str
    description: Optional[str] = None
    published: bool = False
    questions: List[str] = []
    settings: Dict = {}
    template_id: Optional[str] = None


class SurveyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    settings: Optional[Dict] = None
    template_id: Optional[UUID] = None


class SurveyTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class SurveyDescriptionUpdate(BaseModel):
    description: Optional[str] = None


class SurveySettingsUpdate(BaseModel):
    settings: Dict


class SurveyTemplateUpdate(BaseModel):
    template_id: Optional[UUID] = None


class AddQuestionRequest(BaseModel):
    question_id: UUID


class ReorderQuestionsRequest(BaseModel):
    question_ids: List[UUID]