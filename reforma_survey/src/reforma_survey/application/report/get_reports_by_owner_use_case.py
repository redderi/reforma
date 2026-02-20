from typing import List
from uuid import UUID
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetReportsByOwnerUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID) -> List[Report]:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    reports = await self.repository.get_by_owner(owner_id)
                    return reports
                except Exception:
                    raise
