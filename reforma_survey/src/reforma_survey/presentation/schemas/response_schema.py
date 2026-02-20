from typing import Dict, Any
from pydantic import BaseModel, Field


class ResponseOut(BaseModel):
    id: str
    survey_id: str
    user_id: str | None = None
    anonymous_id: str | None = None
    answers: Dict[str, Any] = Field(default_factory=dict)
    submitted_at: str | None = None

    ip_address: str | None = None  # только для админа/владельца опроса
    fingerprint: str | None = None  # только для админа
    user_agent: str | None = None  # только для админа

    class Config:
        from_attributes = True


class ResponseCreate(BaseModel):
    survey_id: str
    answers: Dict[str, Any] = Field(..., description="question_id → ответ")
    anonymous_id: str | None = Field(None, description="FingerprintJS ID для анонимов")
    fingerprint: str | None = None


class ResponseUpdate(BaseModel):
    answers: Dict[str, Any] = Field(..., description="question_id → ответ")
