from uuid import UUID
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class SetSurveyTemplateUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, survey_id: UUID, template_id: UUID | None) -> Survey:
        log_info(f"Установка шаблона для опроса {survey_id} → {template_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.set_template(survey_id, template_id)
                    log_info(f"Шаблон для опроса {survey_id} установлен", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка установки шаблона для опроса {survey_id}: {e}", service="survey-service")
                    raise