from fastapi import APIRouter, Depends, HTTPException
from reforma_survey.presentation.schemas.survey_schema import AddQuestionRequest, ReorderQuestionsRequest, SurveyDescriptionUpdate, SurveyOut, SurveySettingsUpdate, SurveyTemplateUpdate, SurveyTitleUpdate
from reforma_survey.presentation.schemas.survey_schema import SurveyCreate
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_survey.infrastructure.repositories.survey_repository_impl import SurveyRepositoryImpl

from reforma_survey.application.survey.get_survey_by_id_use_case import GetSurveyByIdUseCase
from reforma_survey.application.survey.get_surveys_by_owner_use_case import GetSurveysByOwnerUseCase
from reforma_survey.application.survey.get_published_surveys_use_case import GetPublishedSurveysUseCase
from reforma_survey.application.survey.create_survey_use_case import CreateSurveyUseCase
from reforma_survey.application.survey.update_survey_title_use_case import UpdateSurveyTitleUseCase
from reforma_survey.application.survey.update_survey_description_use_case import UpdateSurveyDescriptionUseCase
from reforma_survey.application.survey.update_survey_settings_use_case import UpdateSurveySettingsUseCase
from reforma_survey.application.survey.set_survey_template_use_case import SetSurveyTemplateUseCase
from reforma_survey.application.survey.publish_survey_use_case import PublishSurveyUseCase
from reforma_survey.application.survey.unpublish_survey_use_case import UnpublishSurveyUseCase
from reforma_survey.application.survey.delete_survey_use_case import DeleteSurveyUseCase
from reforma_survey.application.survey.add_question_to_survey_use_case import AddQuestionToSurveyUseCase
from reforma_survey.application.survey.remove_question_from_survey_use_case import RemoveQuestionFromSurveyUseCase
from reforma_survey.application.survey.reorder_survey_questions_use_case import ReorderSurveyQuestionsUseCase

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Surveys"])

@router.get("/me", response_model=List[SurveyOut])
async def get_my_surveys(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение опросов текущего пользователя {current_user_id}", service="survey-service")

    try:
        use_case = GetSurveysByOwnerUseCase(SurveyRepositoryImpl(db))
        surveys = await use_case.execute(current_user_id)

        return [
            SurveyOut(
                id=str(s.id),
                owner_id=str(s.owner_id),
                title=s.title,
                description=s.description,
                published=s.published,
                questions=[str(q) for q in s.questions],
                settings=s.settings,
                template_id=str(s.template_id) if s.template_id else None,
            )
            for s in surveys
        ]

    except Exception as e:
        log_error(f"Ошибка получения опросов пользователя {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/{survey_id}", response_model=SurveyOut)
async def get_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = GetSurveyByIdUseCase(SurveyRepositoryImpl(db))
        survey = await use_case.execute(survey_id)

        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")

        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к опросу")

        return SurveyOut(
            id=str(survey.id),
            owner_id=str(survey.owner_id),
            title=survey.title,
            description=survey.description,
            published=survey.published,
            questions=[str(q) for q in survey.questions],
            settings=survey.settings,
            template_id=str(survey.template_id) if survey.template_id else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/", response_model=SurveyOut, status_code=201)
async def create_survey(
    payload: SurveyCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Создание опроса пользователем {current_user_id}, title={payload.title}", service="survey-service")

    try:
        use_case = CreateSurveyUseCase(SurveyRepositoryImpl(db))
        created = await use_case.execute(payload.dict(), current_user_id)

        return SurveyOut(
            id=str(created.id),
            owner_id=str(created.owner_id),
            title=created.title,
            description=created.description,
            published=created.published,
            questions=[str(q) for q in created.questions],
            settings=created.settings,
            template_id=str(created.template_id) if created.template_id else None,
        )

    except ValueError as e:
        log_warning(f"Ошибка создания опроса: {e}", service="survey-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Неожиданная ошибка создания опроса: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/title", response_model=SurveyOut)
async def update_survey_title(
    survey_id: UUID,
    payload: SurveyTitleUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление заголовка опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateSurveyTitleUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.title)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав на редактирование")

        return SurveyOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            title=updated.title,
            description=updated.description,
            published=updated.published,
            questions=[str(q) for q in updated.questions],
            settings=updated.settings,
            template_id=str(updated.template_id) if updated.template_id else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления заголовка опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/description", response_model=SurveyOut)
async def update_survey_description(
    survey_id: UUID,
    payload: SurveyDescriptionUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление описания опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateSurveyDescriptionUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.description)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return SurveyOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            title=updated.title,
            description=updated.description,
            published=updated.published,
            questions=[str(q) for q in updated.questions],
            settings=updated.settings,
            template_id=str(updated.template_id) if updated.template_id else None,
        )

    except Exception as e:
        log_error(f"Ошибка обновления описания опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/settings", response_model=SurveyOut)
async def update_survey_settings(
    survey_id: UUID,
    payload: SurveySettingsUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление настроек опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateSurveySettingsUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.settings)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return SurveyOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            title=updated.title,
            description=updated.description,
            published=updated.published,
            questions=[str(q) for q in updated.questions],
            settings=updated.settings,
            template_id=str(updated.template_id) if updated.template_id else None,
        )

    except Exception as e:
        log_error(f"Ошибка обновления настроек опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/template", response_model=SurveyOut)
async def set_survey_template(
    survey_id: UUID,
    payload: SurveyTemplateUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Установка шаблона для опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = SetSurveyTemplateUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.template_id)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return SurveyOut(
            id=str(updated.id),
            owner_id=str(updated.owner_id),
            title=updated.title,
            description=updated.description,
            published=updated.published,
            questions=[str(q) for q in updated.questions],
            settings=updated.settings,
            template_id=str(updated.template_id) if updated.template_id else None,
        )

    except Exception as e:
        log_error(f"Ошибка установки шаблона опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{survey_id}/publish")
async def publish_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Публикация опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = PublishSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {"detail": "Опрос опубликован", "published": updated.published}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка публикации опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{survey_id}/unpublish")
async def unpublish_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Снятие с публикации опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UnpublishSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {"detail": "Опрос снят с публикации", "published": updated.published}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка снятия с публикации опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{survey_id}")
async def delete_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = DeleteSurveyUseCase(SurveyRepositoryImpl(db))
        await use_case.execute(survey_id)
        return {"detail": "Опрос удалён"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{survey_id}/questions")
async def add_question_to_survey(
    survey_id: UUID,
    payload: AddQuestionRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Добавление вопроса {payload.question_id} в опрос {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = AddQuestionToSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.question_id)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {
            "detail": "Вопрос добавлен",
            "questions": [str(q) for q in updated.questions]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка добавления вопроса в опрос {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{survey_id}/questions/{question_id}")
async def remove_question_from_survey(
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление вопроса {question_id} из опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = RemoveQuestionFromSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, question_id)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {
            "detail": "Вопрос удалён",
            "questions": [str(q) for q in updated.questions]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления вопроса из опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/reorder-questions")
async def reorder_survey_questions(
    survey_id: UUID,
    payload: ReorderQuestionsRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Переупорядочивание вопросов в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = ReorderSurveyQuestionsUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.question_ids)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {
            "detail": "Порядок вопросов обновлён",
            "questions": [str(q) for q in updated.questions]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка переупорядочивания вопросов опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")