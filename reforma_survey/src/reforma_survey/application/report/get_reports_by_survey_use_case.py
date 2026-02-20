from typing import List
from uuid import UUID
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal


class GetReportsBySurveyUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> List[Report]:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    reports = await self.repository.get_by_survey(survey_id)
                    return reports
                except Exception:
                    raise
