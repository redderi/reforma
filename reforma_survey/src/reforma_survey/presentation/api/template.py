from fastapi import APIRouter, Depends, HTTPException
from reforma_survey.presentation.schemas.template_schema import TemplateAddAsset, TemplateCreate, TemplateDescriptionUpdate, TemplateNameUpdate, TemplateOut, TemplateRemoveAsset
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, List

from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_survey.infrastructure.repositories.template_repository_impl import TemplateRepositoryImpl

from reforma_survey.application.template.get_template_by_id_use_case import GetTemplateByIdUseCase
from reforma_survey.application.template.get_templates_by_owner_use_case import GetTemplatesByOwnerUseCase
from reforma_survey.application.template.create_template_use_case import CreateTemplateUseCase
from reforma_survey.application.template.update_template_name_use_case import UpdateTemplateNameUseCase
from reforma_survey.application.template.update_template_description_use_case import UpdateTemplateDescriptionUseCase
from reforma_survey.application.template.update_template_survey_style_use_case import UpdateTemplateSurveyStyleUseCase
from reforma_survey.application.template.update_template_question_style_use_case import UpdateTemplateQuestionStyleUseCase
from reforma_survey.application.template.add_template_asset_use_case import AddTemplateAssetUseCase
from reforma_survey.application.template.remove_template_asset_use_case import RemoveTemplateAssetUseCase
from reforma_survey.application.template.delete_template_use_case import DeleteTemplateUseCase

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("/me", response_model=List[TemplateOut])
async def get_my_templates(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение всех шаблонов пользователя {current_user_id}", service="survey-service")

    try:
        use_case = GetTemplatesByOwnerUseCase(TemplateRepositoryImpl(db))
        templates = await use_case.execute(current_user_id)

        return [
            TemplateOut(
                id=str(t.id),
                owner_id=str(t.owner_id),
                name=t.name,
                description=t.description,
                survey_style=t.survey_style,
                question_style=t.question_style,
                assets=t.assets,
            )
            for t in templates
        ]

    except Exception as e:
        log_error(f"Ошибка получения шаблонов пользователя {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(
    template_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение шаблона {template_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = GetTemplateByIdUseCase(TemplateRepositoryImpl(db))
        template = await use_case.execute(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Шаблон не найден")

        if str(template.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к шаблону")

        return TemplateOut(
            id=str(template.id),
            owner_id=str(template.owner_id),
            name=template.name,
            description=template.description,
            survey_style=template.survey_style,
            question_style=template.question_style,
            assets=template.assets,
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения шаблона {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/", response_model=TemplateOut, status_code=201)
async def create_template(
    payload: TemplateCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Создание шаблона пользователем {current_user_id}, name={payload.name}", service="survey-service")

    try:
        use_case = CreateTemplateUseCase(TemplateRepositoryImpl(db))
        template_data = payload.dict(exclude_unset=True)
        created = await use_case.execute(template_data, current_user_id)

        return TemplateOut(
            id=str(created.id),
            owner_id=str(created.owner_id),
            name=created.name,
            description=created.description,
            survey_style=created.survey_style,
            question_style=created.question_style,
            assets=created.assets,
        )

    except ValueError as e:
        log_warning(f"Ошибка создания шаблона: {e}", service="survey-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Неожиданная ошибка создания шаблона: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{template_id}/name", response_model=TemplateOut)
async def update_template_name(
    template_id: UUID,
    payload: TemplateNameUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление имени шаблона {template_id} → {payload.name} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateTemplateNameUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.name)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав на редактирование")

        return TemplateOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            name=updated.name,
            description=updated.description,
            survey_style=updated.survey_style,
            question_style=updated.question_style,
            assets=updated.assets,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления имени шаблона {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{template_id}/description", response_model=TemplateOut)
async def update_template_description(
    template_id: UUID,
    payload: TemplateDescriptionUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление описания шаблона {template_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateTemplateDescriptionUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.description)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return TemplateOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            name=updated.name,
            description=updated.description,
            survey_style=updated.survey_style,
            question_style=updated.question_style,
            assets=updated.assets,
        )

    except Exception as e:
        log_error(f"Ошибка обновления описания шаблона {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{template_id}/survey-style", response_model=TemplateOut)
async def update_template_survey_style(
    template_id: UUID,
    payload: Dict,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление стилей опроса шаблона {template_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateTemplateSurveyStyleUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return TemplateOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            name=updated.name,
            description=updated.description,
            survey_style=updated.survey_style,
            question_style=updated.question_style,
            assets=updated.assets,
        )

    except Exception as e:
        log_error(f"Ошибка обновления стилей опроса шаблона {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{template_id}/question-style", response_model=TemplateOut)
async def update_template_question_style(
    template_id: UUID,
    payload: Dict,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление стилей вопросов шаблона {template_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateTemplateQuestionStyleUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return TemplateOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            name=updated.name,
            description=updated.description,
            survey_style=updated.survey_style,
            question_style=updated.question_style,
            assets=updated.assets,
        )

    except Exception as e:
        log_error(f"Ошибка обновления стилей вопросов шаблона {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{template_id}/assets")
async def add_template_asset(
    template_id: UUID,
    payload: TemplateAddAsset,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Добавление ассета в шаблон {template_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = AddTemplateAssetUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.asset_url)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {
            "detail": "Ассет добавлен",
            "assets": updated.assets
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка добавления ассета в шаблон {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{template_id}/assets")
async def remove_template_asset(
    template_id: UUID,
    payload: TemplateRemoveAsset,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление ассета из шаблона {template_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = RemoveTemplateAssetUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.asset_url)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {
            "detail": "Ассет удалён",
            "assets": updated.assets
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления ассета из шаблона {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление шаблона {template_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = DeleteTemplateUseCase(TemplateRepositoryImpl(db))
        await use_case.execute(template_id)

        return {"detail": "Шаблон удалён"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления шаблона {template_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")