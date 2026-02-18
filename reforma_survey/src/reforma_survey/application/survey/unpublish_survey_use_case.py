from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class UnpublishSurveyUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> Survey:
        log_info(f"Начало снятия с публикации опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.unpublish(survey_id)
                    log_info(f"Опрос {survey_id} успешно снят с публикации", service="survey-service")
                    return updated
                except ValueError as ve:
                    log_warning(f"Не удалось снять с публикации опрос {survey_id}: {ve}", service="survey-service")
                    raise
                except Exception as e:
                    log_error(f"Ошибка снятия с публикации опроса {survey_id}: {e}", service="survey-service")
                    raise