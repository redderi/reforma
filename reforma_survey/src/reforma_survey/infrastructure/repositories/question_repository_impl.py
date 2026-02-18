from typing import Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload

from reforma_survey.domain.entities.question import Question
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.db.models import QuestionModel, BranchingRuleModel


class QuestionRepositoryImpl(QuestionRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, question_id: UUID) -> Question | None:
        result = await self.db.execute(
            select(QuestionModel)
            .where(QuestionModel.id == question_id)
            .options(selectinload(QuestionModel.branching_rules))
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_survey(self, survey_id: UUID) -> List[Question]:
        result = await self.db.execute(
            select(QuestionModel)
            .where(QuestionModel.survey_id == survey_id)
            .options(selectinload(QuestionModel.branching_rules))
            .order_by(QuestionModel.order)
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_survey_ordered(self, survey_id: UUID) -> List[Question]:
        return await self.get_by_survey(survey_id)

    async def create(self, question: Question) -> Question:
        model = QuestionModel(
            id=question.id,
            survey_id=question.survey_id,
            question_text=question.text,
            answer_type=question.type,
            options=question.options,
            style=question.style,
            order=question.order,
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def update_text(self, question_id: UUID, new_text: str) -> Question:
        model = await self._get_model_or_raise(question_id)
        model.question_text = new_text.strip()
        await self.db.flush()
        return self._to_entity(model)

    async def update_type(self, question_id: UUID, new_type: str) -> Question:
        model = await self._get_model_or_raise(question_id)
        model.answer_type = new_type.strip()
        await self.db.flush()
        return self._to_entity(model)

    async def update_options(self, question_id: UUID, options: List[str]) -> Question:
        model = await self._get_model_or_raise(question_id)
        model.options = options
        await self.db.flush()
        return self._to_entity(model)

    async def update_style(self, question_id: UUID, style: Dict) -> Question:
        model = await self._get_model_or_raise(question_id)
        model.style = style
        await self.db.flush()
        return self._to_entity(model)

    async def update_order(self, question_id: UUID, new_order: int) -> Question:
        model = await self._get_model_or_raise(question_id)
        model.order = new_order
        await self.db.flush()
        return self._to_entity(model)

    async def delete(self, question_id: UUID) -> None:
        stmt = delete(QuestionModel).where(QuestionModel.id == question_id)
        await self.db.execute(stmt)

    async def exists(self, question_id: UUID) -> bool:
        result = await self.db.execute(
            select(1)
            .select_from(QuestionModel)
            .where(QuestionModel.id == question_id)
            .limit(1)
        )
        return result.scalar() is not None

    async def count_by_survey(self, survey_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(QuestionModel)
            .where(QuestionModel.survey_id == survey_id)
        )
        return result.scalar() or 0


    async def _get_model_or_raise(self, question_id: UUID) -> QuestionModel:
        model = await self.db.get(QuestionModel, question_id)
        if not model:
            raise ValueError(f"Вопрос с id {question_id} не найден")
        return model

    def _to_entity(self, model: QuestionModel) -> Question:
        next_questions = {}
        for rule in model.branching_rules:
            condition = rule.condition or {}
            answer = condition.get("answer")
            next_id = condition.get("next_question_id")
            if answer and next_id:
                next_questions[answer] = UUID(next_id)

            if condition.get("is_default"):
                next_questions["default"] = UUID(next_id)

        return Question(
            id=model.id,
            survey_id=model.survey_id,
            text=model.question_text,
            type=model.answer_type,
            options=model.options or [],
            style=model.style or {},
            order=model.order,
            next_questions=next_questions,
        )