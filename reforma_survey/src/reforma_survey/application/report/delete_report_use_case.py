from uuid import UUID
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error

# TODO добавить удаление связных файлов в s3

class DeleteReportUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, report_id: UUID) -> None:
        log_info(f"Удаление отчёта {report_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    await self.repository.delete(report_id)
                    log_info(f"Отчёт {report_id} успешно удалён", service="survey-service")
                except Exception as e:
                    log_error(f"Ошибка удаления отчёта {report_id}: {e}", service="survey-service")
                    raise