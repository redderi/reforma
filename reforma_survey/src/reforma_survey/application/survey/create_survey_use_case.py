from uuid import UUID
from typing import Dict, Any
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class CreateSurveyUseCase:
    def __init__(self, repository: SurveyRepository):
        self.repository = repository

    async def execute(self, data: Dict[str, Any], owner_id: UUID) -> Survey:
        log_info(f"Начало создания опроса для owner_id={owner_id}, title={data.get('title')}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    survey = Survey(
                        id=UUID(),
                        owner_id=owner_id,
                        title=data.get("title", "").strip(),
                        description=data.get("description"),
                        settings=data.get("settings", {}),
                        template_id=data.get("template_id"),
                        published=False,
                        questions=[],
                    )

                    if not survey.title:
                        raise ValueError("Заголовок опроса обязателен")

                    created = await self.repository.create(survey)

                    log_info(f"Опрос успешно создан: id={created.id}, title={created.title}", service="survey-service")
                    return created

                except ValueError as ve:
                    log_error(f"Ошибка валидации при создании опроса: {ve}", service="survey-service")
                    raise
                except Exception as e:
                    log_error(f"Неожиданная ошибка при создании опроса: {e}", service="survey-service")
                    raise