from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from reforma_survey.domain.entities.branching_rule import BranchingRule
from reforma_survey.domain.repositories.branching_rule_repository import (
    BranchingRuleRepository,
)
from reforma_survey.infrastructure.db.models import BranchingRuleModel


class BranchingRuleRepositoryImpl(BranchingRuleRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, rule_id: UUID) -> BranchingRule | None:
        result = await self.db.execute(
            select(BranchingRuleModel).where(BranchingRuleModel.id == rule_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_question(self, question_id: UUID) -> List[BranchingRule]:
        result = await self.db.execute(
            select(BranchingRuleModel)
            .where(BranchingRuleModel.question_id == question_id)
            .order_by(BranchingRuleModel.is_default.desc()) 
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_default_for_question(self, question_id: UUID) -> BranchingRule | None:
        result = await self.db.execute(
            select(BranchingRuleModel)
            .where(BranchingRuleModel.question_id == question_id)
            .where(BranchingRuleModel.is_default)
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def create(self, rule: BranchingRule) -> BranchingRule:
        model = BranchingRuleModel(
            id=rule.id,
            question_id=rule.question_id,
            condition={
                "answer": rule.answer_value,
                "next_question_id": str(rule.next_question_id),
                "is_default": rule.is_default,
            },
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def update_answer_value(
        self, rule_id: UUID, new_answer_value: str
    ) -> BranchingRule:
        model = await self._get_model_or_raise(rule_id)
        condition = model.condition or {}
        condition["answer"] = new_answer_value.strip()
        model.condition = condition
        await self.db.flush()
        return self._to_entity(model)

    async def update_next_question(
        self, rule_id: UUID, new_next_question_id: UUID
    ) -> BranchingRule:
        model = await self._get_model_or_raise(rule_id)
        condition = model.condition or {}
        condition["next_question_id"] = str(new_next_question_id)
        model.condition = condition
        await self.db.flush()
        return self._to_entity(model)

    async def set_default(
        self, rule_id: UUID, is_default: bool = True
    ) -> BranchingRule:
        model = await self._get_model_or_raise(rule_id)
        condition = model.condition or {}
        condition["is_default"] = is_default
        model.condition = condition
        await self.db.flush()
        return self._to_entity(model)

    async def delete(self, rule_id: UUID) -> None:
        stmt = delete(BranchingRuleModel).where(BranchingRuleModel.id == rule_id)
        await self.db.execute(stmt)

    async def exists(self, rule_id: UUID) -> bool:
        result = await self.db.execute(
            select(1)
            .select_from(BranchingRuleModel)
            .where(BranchingRuleModel.id == rule_id)
            .limit(1)
        )
        return result.scalar() is not None

    async def count_by_question(self, question_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(BranchingRuleModel)
            .where(BranchingRuleModel.question_id == question_id)
        )
        return result.scalar() or 0

    async def _get_model_or_raise(self, rule_id: UUID) -> BranchingRuleModel:
        model = await self.db.get(BranchingRuleModel, rule_id)
        if not model:
            raise ValueError(f"Правило ветвления с id {rule_id} не найдено")
        return model

    def _to_entity(self, model: BranchingRuleModel) -> BranchingRule:
        condition = model.condition or {}
        return BranchingRule(
            id=model.id,
            question_id=model.question_id,
            answer_value=condition.get("answer", ""),
            next_question_id=UUID(condition.get("next_question_id", "")),
            is_default=condition.get("is_default", False),
        )
