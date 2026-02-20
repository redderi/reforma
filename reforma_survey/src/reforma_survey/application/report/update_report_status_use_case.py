from uuid import UUID
from datetime import datetime
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class UpdateReportStatusUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(
        self,
        report_id: UUID,
        new_status: str,
        processing_started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> Report:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_status(
                        report_id,
                        new_status,
                        processing_started_at,
                        completed_at,
                        error_message,
                    )
                    return updated
                except Exception:
                    raise
