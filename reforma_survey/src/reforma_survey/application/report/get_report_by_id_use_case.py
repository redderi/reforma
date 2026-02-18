from typing import Optional
from uuid import UUID

from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_warning, log_error


class GetReportByIdUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, report_id: UUID) -> Optional[Report]:
        log_info(f"Получение отчёта по ID: {report_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    report = await self.repository.get_by_id(report_id)
                    if report:
                        log_info(f"Отчёт найден: {report_id}, status={report.status}", service="survey-service")
                    else:
                        log_warning(f"Отчёт не найден: {report_id}", service="survey-service")
                    return report
                except Exception as e:
                    log_error(f"Ошибка получения отчёта {report_id}: {e}", service="survey-service")
                    raise