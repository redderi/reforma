from typing import Dict, List
from pydantic import BaseModel, Field


class TemplateOut(BaseModel):
    id: str
    owner_id: str
    name: str
    description: str | None = None
    survey_style: Dict = {}
    question_style: Dict = {}
    assets: List[str] = []


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    survey_style: Dict | None = None
    question_style: Dict | None = None
    assets: List[str] | None = None


class TemplateNameUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class TemplateDescriptionUpdate(BaseModel):
    description: str | None = None


class TemplateSurveyStyleUpdate(BaseModel):
    survey_style: Dict


class TemplateQuestionStyleUpdate(BaseModel):
    question_style: Dict


class TemplateAddAsset(BaseModel):
    asset_url: str


class TemplateRemoveAsset(BaseModel):
    asset_url: str
