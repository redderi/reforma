from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class RemoveQuestionFromSurveyUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, question_id: UUID) -> Survey:
        log_info(f"Начало удаления вопроса {question_id} из опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.remove_question(survey_id, question_id)
                    log_info(f"Вопрос {question_id} успешно удалён из опроса {survey_id}", service="survey-service")
                    return updated
                except ValueError as ve:
                    log_error(f"Ошибка удаления вопроса из опроса {survey_id}: {ve}", service="survey-service")
                    raise
                except Exception as e:
                    log_error(f"Неожиданная ошибка удаления вопроса из опроса {survey_id}: {e}", service="survey-service")
                    raise