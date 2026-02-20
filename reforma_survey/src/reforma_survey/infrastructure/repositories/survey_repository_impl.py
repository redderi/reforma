from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload
from reforma_survey.domain.entities.survey import Survey
from reforma_survey.domain.repositories.survey_repository import SurveyRepository
from reforma_survey.infrastructure.db.models import SurveyModel, QuestionModel


class SurveyRepositoryImpl(SurveyRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, survey_id: UUID) -> Survey | None:
        result = await self.db.execute(
            select(SurveyModel)
            .where(SurveyModel.id == survey_id)
            .options(selectinload(SurveyModel.questions))
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model, load_questions=True)

    async def get_by_owner(self, owner_id: UUID) -> List[Survey]:
        result = await self.db.execute(
            select(SurveyModel)
            .where(SurveyModel.owner_id == owner_id)
            .options(selectinload(SurveyModel.questions))
            .order_by(SurveyModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m, load_questions=True) for m in models]

    async def get_published_by_owner(self, owner_id: UUID) -> List[Survey]:
        result = await self.db.execute(
            select(SurveyModel)
            .where(SurveyModel.owner_id == owner_id)
            .where(SurveyModel.published)
            .options(selectinload(SurveyModel.questions))
            .order_by(SurveyModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m, load_questions=True) for m in models]

    async def get_published(self) -> List[Survey]:
        result = await self.db.execute(
            select(SurveyModel)
            .where(SurveyModel.published)
            .options(selectinload(SurveyModel.questions))
            .order_by(SurveyModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m, load_questions=True) for m in models]

    async def create(self, survey: Survey) -> Survey:
        model = SurveyModel(
            id=survey.id,
            owner_id=survey.owner_id,
            title=survey.title,
            description=survey.description,
            settings=survey.settings,
            template_id=survey.template_id,
            published=survey.published,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_title(self, survey_id: UUID, new_title: str) -> Survey:
        model = await self._get_model_or_raise(survey_id)
        model.title = new_title.strip()
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_description(
        self, survey_id: UUID, description: str | None
    ) -> Survey:
        model = await self._get_model_or_raise(survey_id)
        model.description = description
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def update_settings(self, survey_id: UUID, settings: dict) -> Survey:
        model = await self._get_model_or_raise(survey_id)
        model.settings = settings
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def set_template(self, survey_id: UUID, template_id: UUID | None) -> Survey:
        model = await self._get_model_or_raise(survey_id)
        model.template_id = template_id
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def publish(self, survey_id: UUID) -> Survey:
        model = await self._get_model_or_raise(survey_id)
        if model.published:
            raise ValueError("Опрос уже опубликован")
        model.published = True
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def unpublish(self, survey_id: UUID) -> Survey:
        model = await self._get_model_or_raise(survey_id)
        if not model.published:
            raise ValueError("Опрос не опубликован")
        model.published = False
        await self.db.flush()
        await self.db.commit()
        return self._to_entity(model)

    async def delete(self, survey_id: UUID) -> None:
        stmt = delete(SurveyModel).where(SurveyModel.id == survey_id)
        await self.db.execute(stmt)
        await self.db.flush()
        await self.db.commit()

    async def add_question(self, survey_id: UUID, question_id: UUID) -> Survey:

        exists = await self.db.execute(
            select(1)
            .select_from(QuestionModel)
            .where(QuestionModel.id == question_id)
            .limit(1)
        )
        if not exists.scalar():
            raise ValueError(f"Вопрос с id {question_id} не найден")

        result = await self.db.execute(
            update(QuestionModel)
            .where(QuestionModel.id == question_id)
            .values(survey_id=survey_id)
        )

        if result.rowcount == 0:
            raise RuntimeError(f"Не удалось привязать вопрос {question_id}")

        await self.db.flush()
        await self.db.commit()
        return await self.get_by_id(survey_id)

    async def remove_question(self, survey_id: UUID, question_id: UUID) -> Survey:

        result = await self.db.execute(
            update(QuestionModel)
            .where(QuestionModel.id == question_id)
            .where(QuestionModel.survey_id == survey_id)
            .values(survey_id=None)
        )

        if result.rowcount == 0:
            raise ValueError(
                f"Вопрос {question_id} не найден или не принадлежит опросу {survey_id}"
            )

        await self.db.flush()
        await self.db.commit()
        return await self.get_by_id(survey_id)

    async def reorder_questions(
        self, survey_id: UUID, question_ids: List[UUID]
    ) -> Survey:

        result = await self.db.execute(
            select(QuestionModel.id).where(QuestionModel.survey_id == survey_id)
        )
        existing_ids = {row[0] for row in result.fetchall()}

        incoming_ids = set(question_ids)
        if incoming_ids != existing_ids:
            raise ValueError(
                f"Список question_ids не совпадает с текущими вопросами опроса. "
                f"Ожидалось {existing_ids}, получено {incoming_ids}"
            )

        for new_order, q_id in enumerate(question_ids):
            await self.db.execute(
                update(QuestionModel)
                .where(QuestionModel.id == q_id)
                .values(order=new_order)
            )

        await self.db.flush()
        await self.db.commit()
        return await self.get_by_id(survey_id)

    async def exists(self, survey_id: UUID) -> bool:
        result = await self.db.execute(
            select(1)
            .select_from(SurveyModel)
            .where(SurveyModel.id == survey_id)
            .limit(1)
        )
        return result.scalar() is not None

    async def count_by_owner(self, owner_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(SurveyModel)
            .where(SurveyModel.owner_id == owner_id)
        )
        return result.scalar() or 0

    async def _get_model_or_raise(self, survey_id: UUID) -> SurveyModel:
        model = await self.db.get(SurveyModel, survey_id)
        if not model:
            raise ValueError(f"Опрос с id {survey_id} не найден")
        return model

    def _to_entity(self, model: SurveyModel, load_questions: bool = False) -> Survey:
        questions_ids = []
        if load_questions and model.questions is not None:
            sorted_questions = sorted(model.questions, key=lambda q: q.order)
            questions_ids = [q.id for q in sorted_questions]

        return Survey(
            id=model.id,
            owner_id=model.owner_id,
            title=model.title,
            description=model.description,
            questions=questions_ids,
            settings=model.settings or {},
            template_id=model.template_id,
            published=model.published,
        )
