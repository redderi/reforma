from typing import List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func

from reforma_survey.domain.entities.report import Report
from reforma_survey.domain.repositories.report_repository import ReportRepository
from reforma_survey.infrastructure.db.models import ReportModel


class ReportRepositoryImpl(ReportRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, report_id: UUID) -> Report | None:
        result = await self.db.execute(
            select(ReportModel).where(ReportModel.id == report_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_survey(self, survey_id: UUID) -> List[Report]:
        result = await self.db.execute(
            select(ReportModel)
            .where(ReportModel.survey_id == survey_id)
            .order_by(ReportModel.requested_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_owner(self, owner_id: UUID) -> List[Report]:
        result = await self.db.execute(
            select(ReportModel)
            .where(ReportModel.owner_id == owner_id)
            .order_by(ReportModel.requested_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_latest_by_survey(self, survey_id: UUID) -> Report | None:
        result = await self.db.execute(
            select(ReportModel)
            .where(ReportModel.survey_id == survey_id)
            .order_by(ReportModel.requested_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)


    async def create(self, report: Report) -> Report:
        model = ReportModel(
            id=report.id,
            survey_id=report.survey_id,
            owner_id=report.owner_id,
            requested_at=report.requested_at,
            status=report.status,
            report_type=report.report_type,
            processing_started_at=report.processing_started_at,
            completed_at=report.completed_at,
            file_urls=report.file_urls,
            error_message=report.error_message,
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def update_status(
        self,
        report_id: UUID,
        new_status: str,
        processing_started_at: datetime | None = None,
        completed_at: datetime | None = None,
        error_message: str | None = None
    ) -> Report:
        model = await self._get_model_or_raise(report_id)

        model.status = new_status

        if processing_started_at is not None:
            model.processing_started_at = processing_started_at

        if completed_at is not None:
            model.completed_at = completed_at

        if error_message is not None:
            model.error_message = error_message

        await self.db.flush()
        return self._to_entity(model)

    async def add_file_url(self, report_id: UUID, file_url: str) -> Report:
        model = await self._get_model_or_raise(report_id)
        if file_url not in model.file_urls:
            model.file_urls.append(file_url)
        await self.db.flush()
        return self._to_entity(model)

    async def set_file_urls(self, report_id: UUID, file_urls: List[str]) -> Report:
        model = await self._get_model_or_raise(report_id)
        model.file_urls = file_urls
        await self.db.flush()
        return self._to_entity(model)

    async def delete(self, report_id: UUID) -> None:
        stmt = delete(ReportModel).where(ReportModel.id == report_id)
        await self.db.execute(stmt)

    async def exists(self, report_id: UUID) -> bool:
        result = await self.db.execute(
            select(1).select_from(ReportModel).where(ReportModel.id == report_id).limit(1)
        )
        return result.scalar() is not None

    async def count_by_survey(self, survey_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(ReportModel).where(ReportModel.survey_id == survey_id)
        )
        return result.scalar() or 0

    async def count_by_owner(self, owner_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(ReportModel).where(ReportModel.owner_id == owner_id)
        )
        return result.scalar() or 0

    async def _get_model_or_raise(self, report_id: UUID) -> ReportModel:
        model = await self.db.get(ReportModel, report_id)
        if not model:
            raise ValueError(f"Отчёт с id {report_id} не найден")
        return model

    def _to_entity(self, model: ReportModel) -> Report:
        return Report(
            id=model.id,
            survey_id=model.survey_id,
            owner_id=model.owner_id,
            requested_at=model.requested_at,
            status=model.status,
            report_type=model.report_type,
            processing_started_at=model.processing_started_at,
            completed_at=model.completed_at,
            file_urls=model.file_urls,
            error_message=model.error_message,
        )