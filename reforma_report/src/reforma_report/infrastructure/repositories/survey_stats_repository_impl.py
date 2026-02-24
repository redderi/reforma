from uuid import UUID
from typing import Optional
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_report.domain.entities.survey_stats import SurveyStats
from reforma_report.domain.repositories.survey_stats_repository import SurveyStatsRepository
from reforma_report.infrastructure.db.models import SurveyStatModel


class SurveyStatsRepositoryImpl(SurveyStatsRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, survey_id: UUID) -> Optional[SurveyStats]:
        result = await self.db.execute(
            select(SurveyStatModel).where(SurveyStatModel.survey_id == survey_id)
        )
        row = result.scalar_one_or_none()
        if row:
            return SurveyStats(
                id=row.id,
                survey_id=row.survey_id,
                owner_id=row.owner_id,
                allowed_user_ids=row.allowed_user_ids or [],
                total_responses=row.total_responses,
                sum_per_type=row.sum_per_type or {},
                sum_of_squares_per_type=row.sum_of_squares_per_type or {},
                min_per_type=row.min_per_type or {},
                max_per_type=row.max_per_type or {},
                sentiment_summary=row.sentiment_summary,
                keyword_analysis=row.keyword_analysis,
                recommendations=row.recommendations or [],
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
        return None

    async def create(self, survey_stats: SurveyStats) -> None:
        stmt = insert(SurveyStatModel).values(
            id=survey_stats.id,
            survey_id=survey_stats.survey_id,
            owner_id=survey_stats.owner_id,
            allowed_user_ids=survey_stats.allowed_user_ids,
            total_responses=survey_stats.total_responses,
            sum_per_type=survey_stats.sum_per_type,
            sum_of_squares_per_type=survey_stats.sum_of_squares_per_type,
            min_per_type=survey_stats.min_per_type,
            max_per_type=survey_stats.max_per_type,
            sentiment_summary=survey_stats.sentiment_summary,
            keyword_analysis=survey_stats.keyword_analysis,
            recommendations=survey_stats.recommendations,
            created_at=survey_stats.created_at,
            updated_at=survey_stats.updated_at,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def update(self, survey_stats: SurveyStats) -> None:
        stmt = (
            update(SurveyStatModel)
            .where(SurveyStatModel.id == survey_stats.id)
            .values(
                allowed_user_ids=survey_stats.allowed_user_ids,
                total_responses=survey_stats.total_responses,
                sum_per_type=survey_stats.sum_per_type,
                sum_of_squares_per_type=survey_stats.sum_of_squares_per_type,
                min_per_type=survey_stats.min_per_type,
                max_per_type=survey_stats.max_per_type,
                sentiment_summary=survey_stats.sentiment_summary,
                keyword_analysis=survey_stats.keyword_analysis,
                recommendations=survey_stats.recommendations,
                updated_at=survey_stats.updated_at,
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def add_allowed_user(self, survey_id: UUID, user_id: UUID) -> None:
        survey_stats = await self.get(survey_id)
        if survey_stats and user_id not in survey_stats.allowed_user_ids:
            survey_stats.allowed_user_ids.append(user_id)
            await self.update(survey_stats)

    async def remove_allowed_user(self, survey_id: UUID, user_id: UUID) -> None:
        survey_stats = await self.get(survey_id)
        if survey_stats and user_id in survey_stats.allowed_user_ids:
            survey_stats.allowed_user_ids.remove(user_id)
            await self.update(survey_stats)

    async def user_has_access(self, survey_id: UUID, user_id: UUID) -> bool:
        survey_stats = await self.get(survey_id)
        if not survey_stats:
            return False
        return user_id == survey_stats.owner_id or user_id in survey_stats.allowed_user_ids