import uuid
from datetime import datetime
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_common.logger import log_info, log_warning
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
        report_type: str = "pdf"
    ) -> Report:
        log_info(
            f"Запрос на генерацию отчёта по опросу {survey_id} от пользователя {owner_id}, тип={report_type}",
            service="survey-service"
        )

        survey = await self.survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(f"Опрос {survey_id} не найден при запросе отчёта", service="survey-service")
            raise ValueError("Опрос не найден")

        if survey.owner_id != owner_id:
            log_warning(f"Пользователь {owner_id} пытается запросить отчёт по чужому опросу {survey_id}", service="survey-service")
            raise ValueError("Нет прав на генерацию отчёта по этому опросу")

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
            f"Отчёт успешно создан в статусе pending: report_id={created_report.id}",
            service="survey-service"
        )

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
            f"Событие ReportGenerationRequested опубликовано для report_id={created_report.id}",
            service="survey-service"
        )

        return created_report