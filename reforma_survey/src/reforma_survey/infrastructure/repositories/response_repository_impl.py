from typing import Dict, List, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, distinct

from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.models import ResponseModel


class ResponseRepositoryImpl(ResponseRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, response_id: UUID) -> Response | None:
        result = await self.db.execute(
            select(ResponseModel).where(ResponseModel.id == response_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_survey(self, survey_id: UUID) -> List[Response]:
        result = await self.db.execute(
            select(ResponseModel)
            .where(ResponseModel.survey_id == survey_id)
            .order_by(ResponseModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_user_and_survey(self, user_id: UUID, survey_id: UUID) -> Response | None:
        result = await self.db.execute(
            select(ResponseModel)
            .where(ResponseModel.user_id == user_id)
            .where(ResponseModel.survey_id == survey_id)
            .order_by(ResponseModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_user(self, user_id: UUID) -> List[Response]:
        result = await self.db.execute(
            select(ResponseModel)
            .where(ResponseModel.user_id == user_id)
            .order_by(ResponseModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def create(self, response: Response) -> Response:
        model = ResponseModel(
            id=response.id,
            survey_id=response.survey_id,
            user_id=response.user_id,
            answers=response.answers,
            created_at=datetime.utcnow(),
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def update_answers(self, response_id: UUID, new_answers: Dict[UUID, Any]) -> Response:
        model = await self._get_model_or_raise(response_id)
        model.answers = new_answers
        await self.db.flush()
        return self._to_entity(model)

    async def mark_submitted(self, response_id: UUID, submitted_at: datetime) -> Response:
        model = await self._get_model_or_raise(response_id)
        model.submitted_at = submitted_at
        await self.db.flush()
        return self._to_entity(model)

    async def delete(self, response_id: UUID) -> None:
        stmt = delete(ResponseModel).where(ResponseModel.id == response_id)
        await self.db.execute(stmt)

    async def exists(self, response_id: UUID) -> bool:
        result = await self.db.execute(
            select(1)
            .select_from(ResponseModel)
            .where(ResponseModel.id == response_id)
            .limit(1)
        )
        return result.scalar() is not None

    async def count_by_survey(self, survey_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(ResponseModel)
            .where(ResponseModel.survey_id == survey_id)
        )
        return result.scalar() or 0

    async def count_by_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(ResponseModel)
            .where(ResponseModel.user_id == user_id)
        )
        return result.scalar() or 0

    async def count_unique_users_by_survey(self, survey_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(distinct(ResponseModel.user_id)))
            .where(ResponseModel.survey_id == survey_id)
        )
        return result.scalar() or 0

    async def _get_model_or_raise(self, response_id: UUID) -> ResponseModel:
        model = await self.db.get(ResponseModel, response_id)
        if not model:
            raise ValueError(f"Ответ с id {response_id} не найден")
        return model

    def _to_entity(self, model: ResponseModel) -> Response:
        return Response(
            id=model.id,
            survey_id=model.survey_id,
            user_id=model.user_id,
            answers=model.answers or {},
            submitted_at=model.submitted_at,
        )