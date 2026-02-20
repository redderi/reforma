from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from typing import List, Optional


@dataclass
class Report:
    id: UUID
    survey_id: UUID
    owner_id: UUID

    requested_at: datetime
    report_type: str = "pdf"  # pdf, excel, pptx, json, dashboard...
    status: str = "pending"  # pending, processing, ready, failed
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    file_urls: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
