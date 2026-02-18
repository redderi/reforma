from typing import Dict, Any, Optional

from pydantic import BaseModel

class ResponseOut(BaseModel):
    id: str
    survey_id: str
    user_id: str
    answers: Dict[str, Any] = {}  # question_id -> ответ
    submitted_at: Optional[str] = None  # isoformat


class ResponseCreate(BaseModel):
    answers: Dict[str, Any]  # question_id -> ответ


class ResponseUpdate(BaseModel):
    answers: Dict[str, Any]