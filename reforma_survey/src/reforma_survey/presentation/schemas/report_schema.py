from uuid import UUID
from typing import List
from pydantic import BaseModel, Field

class ReportOut(BaseModel):
    id: str
    survey_id: str
    owner_id: str
    requested_at: str
    status: str
    report_type: str
    processing_started_at: str | None = None
    completed_at: str | None = None
    file_urls: List[str] = []
    error_message: str | None = None


class ReportRequest(BaseModel):
    survey_id: UUID
    report_type: str = Field(default="pdf", description="pdf, excel, pptx, json...")


class ReportStatusUpdate(BaseModel):
    status: str
    processing_started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class ReportFileUrlAdd(BaseModel):
    file_url: str


class ReportFileUrlsSet(BaseModel):
    file_urls: List[str]