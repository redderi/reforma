from uuid import UUID
from reforma_report.domain.repositories.question_stats_repository import (
    QuestionStatsRepository,
)
from reforma_report.infrastructure.db.session import SessionLocal


class RemoveAllowedUserUseCase:
    def __init__(self, repository: QuestionStatsRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, question_id: UUID, user_id: UUID) -> None:
        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.remove_allowed_user(
                        survey_id, question_id, user_id
                    )
                except Exception:
                    raise
