from uuid import UUID
from typing import List
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class SetReportFileUrlsUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, report_id: UUID, file_urls: List[str]) -> Report:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.set_file_urls(report_id, file_urls)
                    return updated
                except Exception:
                    raise
