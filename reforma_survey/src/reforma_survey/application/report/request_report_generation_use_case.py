from uuid import uuid4, UUID
from datetime import datetime
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_survey.infrastructure.config.rabbitmq_config import (
    REPORT_EXCHANGE,
    REPORT_GENERATION_ROUTING_KEY,
)


class RequestReportGenerationUseCase:
    def __init__(
        self,
        report_repo: ReportRepository,
        survey_repo: SurveyRepository,
        event_publisher: EventPublisher,
    ):
        self.report_repo = report_repo
        self.survey_repo = survey_repo
        self.event_publisher = event_publisher

    async def execute(
        self,
        survey_id: UUID,
        owner_id: UUID,
        report_type: str = "pdf",  
    ) -> Report:
        async with SessionLocal() as db:
            async with db.begin():
                survey = await self.survey_repo.get_by_id(survey_id)
                if not survey:
                    raise ValueError("Опрос не найден")
                if survey.owner_id != owner_id:
                    raise ValueError("Нет прав на генерацию отчёта этого опроса")
                report = Report(
                    id=uuid4(),
                    survey_id=survey_id,
                    owner_id=owner_id,
                    requested_at=datetime.utcnow(),
                    status="pending",
                    report_type=report_type,
                    file_urls=[],
                    error_message=None,
                )
                created_report = await self.report_repo.create(report)
                try:
                    await self.event_publisher.publish_event(
                        exchange_name=REPORT_EXCHANGE,
                        routing_key=REPORT_GENERATION_ROUTING_KEY,
                        payload={
                            "report_id": str(created_report.id),
                            "survey_id": str(survey_id),
                            "owner_id": str(owner_id),
                            "report_type": report_type,
                            "requested_at": created_report.requested_at.isoformat(),
                        },
                    )
                except Exception:
                    pass

                return created_report
