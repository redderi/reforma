from datetime import datetime
from typing import Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload

from reforma_survey.domain.entities.template import Template
from reforma_survey.domain.repositories.template_repository import TemplateRepository
from reforma_survey.infrastructure.db.models import TemplateModel


class TemplateRepositoryImpl(TemplateRepository):

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, template_id: UUID) -> Template | None:
        result = await self.db.execute(
            select(TemplateModel).where(TemplateModel.id == template_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def get_by_owner(self, owner_id: UUID) -> List[Template]:
        result = await self.db.execute(
            select(TemplateModel)
            .where(TemplateModel.owner_id == owner_id)
            .order_by(TemplateModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_name(self, owner_id: UUID, name: str) -> Template | None:
        result = await self.db.execute(
            select(TemplateModel)
            .where(TemplateModel.owner_id == owner_id)
            .where(TemplateModel.name == name.strip())
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def create(self, template: Template) -> Template:
        model = TemplateModel(
            id=template.id,
            owner_id=template.owner_id,
            name=template.name.strip(),
            description=template.description,
            style=template.survey_style,
            created_at=datetime.utcnow(),
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def update_name(self, template_id: UUID, new_name: str) -> Template:
        model = await self._get_model_or_raise(template_id)
        model.name = new_name.strip()
        await self.db.flush()
        return self._to_entity(model)

    async def update_description(self, template_id: UUID, description: str | None) -> Template:
        model = await self._get_model_or_raise(template_id)
        model.description = description
        await self.db.flush()
        return self._to_entity(model)

    async def update_survey_style(self, template_id: UUID, survey_style: Dict) -> Template:
        model = await self._get_model_or_raise(template_id)
        model.style = survey_style
        await self.db.flush()
        return self._to_entity(model)

    async def update_question_style(self, template_id: UUID, question_style: Dict) -> Template:
        model = await self._get_model_or_raise(template_id)
        current_style = model.style or {}
        current_style["question"] = question_style
        model.style = current_style
        await self.db.flush()
        return self._to_entity(model)

    async def add_asset(self, template_id: UUID, asset_url: str) -> Template:
        model = await self._get_model_or_raise(template_id)
        current_style = model.style or {}
        current_assets = current_style.get("assets", [])
        if asset_url not in current_assets:
            current_assets.append(asset_url)
            current_style["assets"] = current_assets
            model.style = current_style
        await self.db.flush()
        return self._to_entity(model)

    async def remove_asset(self, template_id: UUID, asset_url: str) -> Template:
        model = await self._get_model_or_raise(template_id)
        current_style = model.style or {}
        current_assets = current_style.get("assets", [])
        if asset_url in current_assets:
            current_assets.remove(asset_url)
            current_style["assets"] = current_assets
            model.style = current_style
        await self.db.flush()
        return self._to_entity(model)

    async def delete(self, template_id: UUID) -> None:
        stmt = delete(TemplateModel).where(TemplateModel.id == template_id)
        await self.db.execute(stmt)

    async def exists(self, template_id: UUID) -> bool:
        result = await self.db.execute(
            select(1)
            .select_from(TemplateModel)
            .where(TemplateModel.id == template_id)
            .limit(1)
        )
        return result.scalar() is not None

    async def count_by_owner(self, owner_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(TemplateModel)
            .where(TemplateModel.owner_id == owner_id)
        )
        return result.scalar() or 0

    async def _get_model_or_raise(self, template_id: UUID) -> TemplateModel:
        model = await self.db.get(TemplateModel, template_id)
        if not model:
            raise ValueError(f"Шаблон с id {template_id} не найден")
        return model

    def _to_entity(self, model: TemplateModel) -> Template:
        style = model.style or {}
        question_style = style.get("question", {})

        return Template(
            id=model.id,
            owner_id=model.owner_id,
            name=model.name,
            description=model.description,
            survey_style=style,
            question_style=question_style,
            assets=style.get("assets", []),
        )