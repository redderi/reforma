from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetSurveyByIdUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID) -> Survey | None:
        log_info(f"Начало получения опроса по ID: {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    survey = await self.repository.get_by_id(survey_id)
                    if survey:
                        log_info(f"Опрос успешно получен: {survey_id}", service="survey-service")
                    else:
                        log_warning(f"Опрос не найден: {survey_id}", service="survey-service")
                    return survey

                except Exception as e:
                    log_error(f"Ошибка при получении опроса {survey_id}: {e}", service="survey-service")
                    raise