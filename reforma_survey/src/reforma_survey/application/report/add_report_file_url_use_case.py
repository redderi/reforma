from uuid import UUID
from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class AddReportFileUrlUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, report_id: UUID, file_url: str) -> Report:
        log_info(f"Добавление файла {file_url} к отчёту {report_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    updated = await self.repository.add_file_url(report_id, file_url)
                    log_info(f"Файл добавлен к отчёту {report_id}", service="survey-service")
                    return updated
                except Exception as e:
                    log_error(f"Ошибка добавления файла к отчёту {report_id}: {e}", service="survey-service")
                    raise