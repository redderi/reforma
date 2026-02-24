from uuid import UUID
from pydantic import BaseModel, Field


class BranchingRuleOut(BaseModel):
    id: str
    question_id: str
    answer_value: str
    next_question_id: str


class BranchingRuleCreate(BaseModel):
    answer_value: str = Field(..., min_length=1, max_length=100)
    next_question_id: UUID


class BranchingRuleAnswerUpdate(BaseModel):
    answer_value: str = Field(..., min_length=1, max_length=100)


class BranchingRuleNextQuestionUpdate(BaseModel):
    next_question_id: UUID

