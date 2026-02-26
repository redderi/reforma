from typing import Any, List, Dict
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, distinct, or_
from reforma_survey.domain.entities.response import Response
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.db.models import ResponseModel


class ResponseRepositoryImpl(ResponseRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, response_id: UUID) -> Response | None:
        model = await self.db.get(ResponseModel, response_id)
        return self._to_entity(model) if model else None

    async def get_by_survey_with_limit(
        self,
        survey_id: UUID,
        limit: int = 100,
        offset: int = 0,
        include_anonymous: bool = True,
    ) -> List[Response]:
        stmt = (
            select(ResponseModel)
            .where(ResponseModel.survey_id == survey_id)
            .order_by(ResponseModel.submitted_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if not include_anonymous:
            stmt = stmt.where(ResponseModel.user_id.isnot(None))

        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    

    async def get_by_survey(
        self,
        survey_id: UUID,
        include_anonymous: bool = True,
    ) -> List[Response]:
        stmt = (
            select(ResponseModel)
            .where(ResponseModel.survey_id == survey_id)
            .order_by(ResponseModel.submitted_at.desc())
        )

        if not include_anonymous:
            stmt = stmt.where(ResponseModel.user_id.isnot(None))

        result = await self.db.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]
    
    async def get_answers_for_question(
        self,
        survey_id: UUID,
        question_id: UUID,
        include_anonymous: bool = True,
    ) -> List[str]:

        qid_str = str(question_id)

        # Основной запрос: получаем только answers, где есть ключ question_id
        stmt = (
            select(ResponseModel.answers)
            .where(ResponseModel.survey_id == survey_id)
            # Только те ответы, где есть ответ на этот вопрос
            .where(func.jsonb_typeof(ResponseModel.answers) == 'object')
            .where(ResponseModel.answers.has_key(qid_str))
        )

        if not include_anonymous:
            stmt = stmt.where(ResponseModel.user_id.is_not(None))

        result = await self.db.execute(stmt)
        answers_rows = result.scalars().all()

        texts: List[str] = []
        for answers_dict in answers_rows:
            answer = answers_dict.get(qid_str)
            if isinstance(answer, str) and answer.strip():
                texts.append(answer.strip())

        return texts
    

    async def get_by_user_and_survey(
        self,
        survey_id: UUID,
        user_id: UUID | None = None,
        anonymous_id: str | None = None,
    ) -> Response | None:
        stmt = select(ResponseModel).where(ResponseModel.survey_id == survey_id)

        if user_id:
            stmt = stmt.where(ResponseModel.user_id == user_id)
        elif anonymous_id:
            stmt = stmt.where(ResponseModel.anonymous_id == anonymous_id)
        else:
            return None

        stmt = stmt.order_by(ResponseModel.submitted_at.desc()).limit(1)

        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_latest_by_user(
        self, user_id: UUID, limit: int = 10
    ) -> List[Response]:
        result = await self.db.execute(
            select(ResponseModel)
            .where(ResponseModel.user_id == user_id)
            .order_by(ResponseModel.submitted_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def has_already_responded(
        self,
        survey_id: UUID,
        user_id: UUID | None = None,
        anonymous_id: str | None = None,
        ip_address: str | None = None,
        fingerprint: str | None = None,
    ) -> bool:
        if not any([user_id, anonymous_id, ip_address, fingerprint]):
            return False

        stmt = select(ResponseModel.id).where(ResponseModel.survey_id == survey_id)

        conditions = []
        if user_id:
            conditions.append(ResponseModel.user_id == user_id)
        if anonymous_id:
            conditions.append(ResponseModel.anonymous_id == anonymous_id)
        if ip_address:
            conditions.append(ResponseModel.ip_address == ip_address)
        if fingerprint:
            conditions.append(ResponseModel.fingerprint == fingerprint)

        stmt = stmt.where(or_(*conditions)).limit(1)

        result = await self.db.execute(stmt)
        return result.scalar() is not None

    async def create(self, response: Response) -> Response:
        serialized_answers = {str(k): v for k, v in (response.answers or {}).items()}

        model = ResponseModel(
            id=response.id or uuid4(),
            survey_id=response.survey_id,
            user_id=response.user_id,
            anonymous_id=response.anonymous_id,
            ip_address=response.ip_address,
            fingerprint=response.fingerprint,
            answers=serialized_answers,
            submitted_at=response.submitted_at,
        )

        self.db.add(model)
        await self.db.flush()
        await self.db.commit()  # сохраняем изменения
        return self._to_entity(model)

    async def update_answers(
        self, response_id: UUID, new_answers: Dict[UUID, Any]
    ) -> Response:
        model = await self._get_model_or_raise(response_id)
        model.answers = {str(k): v for k, v in new_answers.items()}
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def mark_submitted(
        self, response_id: UUID, submitted_at: datetime | None = None
    ) -> Response:
        model = await self._get_model_or_raise(response_id)
        model.submitted_at = submitted_at or datetime.utcnow()
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def delete(self, response_id: UUID) -> None:
        await self.db.execute(
            delete(ResponseModel).where(ResponseModel.id == response_id)
        )
        await self.db.commit()

    async def count_by_survey(self, survey_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(ResponseModel.survey_id == survey_id)
        )
        return result.scalar() or 0

    async def count_unique_users_by_survey(self, survey_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(distinct(ResponseModel.user_id)))
            .where(ResponseModel.survey_id == survey_id)
            .where(ResponseModel.user_id.isnot(None))
        )
        return result.scalar() or 0

    async def count_by_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).where(ResponseModel.user_id == user_id)
        )
        return result.scalar() or 0

    async def count_anonymous_by_survey(self, survey_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .where(ResponseModel.survey_id == survey_id)
            .where(ResponseModel.user_id.is_(None))
        )
        return result.scalar() or 0

    async def _get_model_or_raise(self, response_id: UUID) -> ResponseModel:
        model = await self.db.get(ResponseModel, response_id)
        if not model:
            raise ValueError(f"Ответ {response_id} не найден")
        return model

    def _to_entity(self, model: ResponseModel) -> Response:
        return Response(
            id=model.id,
            survey_id=model.survey_id,
            user_id=model.user_id,
            anonymous_id=model.anonymous_id,
            ip_address=model.ip_address,
            fingerprint=model.fingerprint,
            answers=model.answers or {},
            submitted_at=model.submitted_at,
        )