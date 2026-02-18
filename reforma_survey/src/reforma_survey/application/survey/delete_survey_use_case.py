from uuid import UUID

from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class DeleteSurveyUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> None:
        log_info(f"Начало удаления опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(survey_id)
                    log_info(f"Опрос {survey_id} успешно удалён", service="survey-service")
                except Exception as e:
                    log_error(f"Ошибка удаления опроса {survey_id}: {e}", service="survey-service")
                    raise