from typing import List
from uuid import UUID

from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.session import SessionLocal
from reforma_common.logger import log_info, log_error


class GetReportsByOwnerUseCase:
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def execute(self, owner_id: UUID) -> List[Report]:
        log_info(f"Получение отчётов владельца {owner_id}", service="survey-service")

        async with SessionLocal() as db:
            async with db.begin():
                try:
                    reports = await self.repository.get_by_owner(owner_id)
                    log_info(f"Получено {len(reports)} отчётов владельца {owner_id}", service="survey-service")
                    return reports
                except Exception as e:
                    log_error(f"Ошибка получения отчётов владельца {owner_id}: {e}", service="survey-service")
                    raise