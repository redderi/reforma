from uuid import UUID

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetResponseByUserAndSurveyUseCase:
    def __init__(self, repository: ResponseRepository):
        self.repository = repository

    async def execute(self, user_id: UUID, survey_id: UUID) -> Response | None:
        log_info(f"Получение ответа пользователя {user_id} на опрос {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    response = await self.repository.get_by_user_and_survey(user_id, survey_id)
                    if response:
                        log_info(f"Ответ пользователя {user_id} на опрос {survey_id} найден", service="survey-service")
                    else:
                        log_warning(f"Ответ пользователя {user_id} на опрос {survey_id} не найден", service="survey-service")
                    return response
                except Exception as e:
                    log_error(f"Ошибка получения ответа пользователя {user_id} на опрос {survey_id}: {e}", service="survey-service")
                    raise