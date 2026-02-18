from uuid import UUID
from typing import List
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class ReorderSurveyQuestionsUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, question_ids: List[UUID]) -> Survey:
        log_info(f"Начало переупорядочивания вопросов в опросе {survey_id} (кол-во: {len(question_ids)})", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.reorder_questions(survey_id, question_ids)
                    log_info(f"Порядок вопросов в опросе {survey_id} успешно обновлён", service="survey-service")
                    return updated
                except ValueError as ve:
                    log_error(f"Ошибка переупорядочивания вопросов в опросе {survey_id}: {ve}", service="survey-service")
                    raise
                except Exception as e:
                    log_error(f"Неожиданная ошибка переупорядочивания вопросов в опросе {survey_id}: {e}", service="survey-service")
                    raise