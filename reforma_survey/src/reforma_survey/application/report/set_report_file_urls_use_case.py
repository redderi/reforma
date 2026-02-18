from uuid import UUID
from typing import List

from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class SetReportFileUrlsUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, report_id: UUID, file_urls: List[str]) -> Report:
        log_info(f"Установка списка файлов для отчёта {report_id} (кол-во: {len(file_urls)})", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.set_file_urls(report_id, file_urls)
                    log_info(f"Список файлов отчёта {report_id} обновлён", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка установки файлов отчёта {report_id}: {e}", service="survey-service")
                    raise