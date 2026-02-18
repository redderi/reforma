from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class UpdateSurveyDescriptionUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, description: str | None) -> Survey:
        log_info(f"Обновление описания опроса {survey_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.update_description(survey_id, description)
                    log_info(f"Описание опроса {survey_id} обновлено", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка обновления описания опроса {survey_id}: {e}", service="survey-service")
                    raise