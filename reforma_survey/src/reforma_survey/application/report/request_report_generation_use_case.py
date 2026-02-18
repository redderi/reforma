import uuid
from datetime import datetime

from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error
from reforma_survey.infrastructure.config.rabbitmq_config import (
    REPORT_EXCHANGE,
    REPORT_GENERATION_ROUTING_KEY
)


class RequestReportGenerationUseCase:
    def __init__(
        self,
        report_repo: ReportRepository,
        survey_repo: SurveyRepository,
        event_publisher: EventPublisher
    ):
        self.report_repo = report_repo
        self.survey_repo = survey_repo
        self.event_publisher = event_publisher

    async def execute(
        self,
        survey_id: uuid.UUID,
        owner_id: uuid.UUID,
        report_type: str = "pdf"  # pdf, excel, pptx
    ) -> Report:
        log_info(
            f"Начало запроса генерации отчёта | survey_id={survey_id} | owner_id={owner_id} | type={report_type}",
            service="survey-service"
        )

        async with SessionLocal() as db:
            async with db.begin():
                # 1. Проверяем опрос и права доступа
                survey = await self.survey_repo.get_by_id(survey_id)
                if not survey:
                    log_warning(f"Опрос {survey_id} не найден", service="survey-service")
                    raise ValueError("Опрос не найден")

                if survey.owner_id != owner_id:
                    log_warning(
                        f"Нет прав: owner_id={owner_id} ≠ survey.owner_id={survey.owner_id}",
                        service="survey-service"
                    )
                    raise ValueError("Нет прав на генерацию отчёта этого опроса")

                # 2. Создаём отчёт в статусе pending
                report = Report(
                    id=uuid.uuid4(),
                    survey_id=survey_id,
                    owner_id=owner_id,
                    requested_at=datetime.utcnow(),
                    status="pending",
                    report_type=report_type,
                    file_urls=[],
                    error_message=None
                )

                created_report = await self.report_repo.create(report)

                log_info(
                    f"Отчёт создан (pending) | report_id={created_report.id} | survey_id={survey_id}",
                    service="survey-service"
                )

                # 3. Публикуем событие в RabbitMQ для reforma-report
                try:
                    await self.event_publisher.publish_event(
                        exchange_name=REPORT_EXCHANGE,
                        routing_key=REPORT_GENERATION_ROUTING_KEY,
                        payload={
                            "report_id": str(created_report.id),
                            "survey_id": str(survey_id),
                            "owner_id": str(owner_id),
                            "report_type": report_type,
                            "requested_at": created_report.requested_at.isoformat()
                        }
                    )

                    log_info(
                        f"Событие ReportGenerationRequested успешно опубликовано | report_id={created_report.id}",
                        service="survey-service"
                    )

                except Exception as e:
                    log_error(
                        f"Ошибка публикации события ReportGenerationRequested | report_id={created_report.id} | {e}",
                        service="survey-service",
                        exc_info=True
                    )
                    # Не откатываем транзакцию — отчёт уже создан, можно будет перезапустить вручную
                    # или добавить retry-механизм

                return created_report