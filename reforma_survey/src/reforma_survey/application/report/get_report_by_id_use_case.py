from typing import Optional
from uuid import UUID
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetReportByIdUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, report_id: UUID) -> Optional[Report]:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    report = await self.repository.get_by_id(report_id)
                    return report
                except Exception:
                    raise
