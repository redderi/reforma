from uuid import UUID
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class AddReportFileUrlUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, report_id: UUID, file_url: str) -> Report:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.add_file_url(report_id, file_url)
                    return updated
                except Exception:
                    raise