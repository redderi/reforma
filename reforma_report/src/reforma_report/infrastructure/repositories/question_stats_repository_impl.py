from uuid import UUID
from typing import Optional, List
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_report.domain.entities.question_stats import QuestionStats
from reforma_report.domain.repositories.question_stats_repository import (
    QuestionStatsRepository,
)
from reforma_report.infrastructure.db.models import QuestionStatModel


class QuestionStatsRepositoryImpl(QuestionStatsRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(
        self, survey_stat_id: UUID, question_id: UUID
    ) -> Optional[QuestionStats]:
        result = await self.db.execute(
            select(QuestionStatModel).where(
                QuestionStatModel.survey_stat_id == survey_stat_id,
                QuestionStatModel.question_id == question_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            return QuestionStats(
                id=row.id,
                survey_stat_id=row.survey_stat_id,  
                question_id=row.question_id,
                type=row.type,
                total=row.total,
                sum=row.sum,
                sum_of_squares=row.sum_of_squares,
                min=row.min,
                max=row.max,
                distribution=row.distribution or {},
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        return None

    async def upsert(self, stats: QuestionStats) -> None:
        existing = await self.get(stats.survey_stat_id, stats.question_id)
        if existing:
            stmt = (
                update(QuestionStatModel)
                .where(
                    QuestionStatModel.survey_stat_id == stats.survey_stat_id,
                    QuestionStatModel.question_id == stats.question_id,
                )
                .values(
                    total=stats.total,
                    sum=stats.sum,
                    sum_of_squares=stats.sum_of_squares,
                    min=stats.min,
                    max=stats.max,
                    distribution=stats.distribution,
                    updated_at=stats.updated_at,
                )
            )
            await self.db.execute(stmt)
        else:
            stmt = insert(QuestionStatModel).values(
                id=stats.id,
                survey_stat_id=stats.survey_stat_id,
                question_id=stats.question_id,
                type=stats.type,
                total=stats.total,
                sum=stats.sum,
                sum_of_squares=stats.sum_of_squares,
                min=stats.min,
                max=stats.max,
                distribution=stats.distribution,
                created_at=stats.created_at,
                updated_at=stats.updated_at,
            )
            await self.db.execute(stmt)
        await self.db.commit()

    async def list_by_survey_stat(self, survey_stat_id: UUID) -> List[QuestionStats]:
        result = await self.db.execute(
            select(QuestionStatModel).where(
                QuestionStatModel.survey_stat_id == survey_stat_id
            )
        )
        rows = result.scalars().all()
        return [
            QuestionStats(
                id=row.id,
                survey_stat_id=row.survey_stat_id,
                question_id=row.question_id,
                type=row.type,
                total=row.total,
                sum=row.sum,
                sum_of_squares=row.sum_of_squares,
                min=row.min,
                max=row.max,
                distribution=row.distribution or {},
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
