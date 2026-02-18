from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateSurveyTitleUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, new_title: str) -> Survey:
        log_info(f"Начало обновления заголовка опроса {survey_id} → {new_title}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_title(survey_id, new_title)
                    log_info(f"Заголовок опроса {survey_id} успешно обновлён", service="survey-service")
                    return updated
                except ValueError as ve:
                    log_error(f"Ошибка валидации заголовка для опроса {survey_id}: {ve}", service="survey-service")
                    raise
                except Exception as e:
                    log_error(f"Ошибка обновления заголовка опроса {survey_id}: {e}", service="survey-service")
                    raise