from uuid import UUID
from reforma_report.infrastructure.db.session import SessionLocal
from reforma_report.domain.repositories.survey_stats_repository import (
    SurveyStatsRepository,
)


class CheckUserAccessUseCase:
    def __init__(self, repository: SurveyStatsRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, user_id: UUID) -> bool:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    return await self.repository.user_has_access(survey_id, user_id)
                except Exception:
                    raise
