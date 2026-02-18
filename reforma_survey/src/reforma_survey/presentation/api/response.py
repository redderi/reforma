from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from reforma_survey.presentation.schemas.response_schema import ResponseCreate, ResponseOut, ResponseUpdate
from reforma_survey.domain.entities.response import Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, Any, List, Optional

from pydantic import BaseModel

from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_survey.infrastructure.repositories.survey_repository_impl import SurveyRepositoryImpl
from reforma_survey.infrastructure.repositories.response_repository_impl import ResponseRepositoryImpl

from reforma_survey.application.response.get_response_by_id_use_case import GetResponseByIdUseCase
from reforma_survey.application.response.get_responses_by_survey_use_case import GetResponsesBySurveyUseCase
from reforma_survey.application.response.get_response_by_user_and_survey_use_case import GetResponseByUserAndSurveyUseCase
from reforma_survey.application.response.get_responses_by_user_use_case import GetResponsesByUserUseCase
from reforma_survey.application.response.create_response_use_case import CreateResponseUseCase
from reforma_survey.application.response.update_response_answers_use_case import UpdateResponseAnswersUseCase
from reforma_survey.application.response.mark_response_submitted_use_case import MarkResponseSubmittedUseCase
from reforma_survey.application.response.delete_response_use_case import DeleteResponseUseCase
from reforma_survey.application.response.response_exists_use_case import ResponseExistsUseCase
from reforma_survey.application.response.count_responses_by_survey_use_case import CountResponsesBySurveyUseCase
from reforma_survey.application.response.count_responses_by_user_use_case import CountResponsesByUserUseCase
from reforma_survey.application.response.count_unique_users_by_survey_use_case import CountUniqueUsersBySurveyUseCase

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Responses"])


@router.get("/{survey_id}/responses", response_model=List[ResponseOut])
async def get_responses_in_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение всех ответов на опрос {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к ответам опроса")

        use_case = GetResponsesBySurveyUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(survey_id)

        return [
            ResponseOut(
                id=str(r.id),
                survey_id=str(r.survey_id),
                user_id=str(r.user_id),
                answers={str(k): v for k, v in r.answers.items()},
                submitted_at=r.submitted_at.isoformat() if r.submitted_at else None,
            )
            for r in responses
        ]

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения ответов на опрос {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/{survey_id}/responses/me", response_model=Optional[ResponseOut])
async def get_my_response_in_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение своего ответа на опрос {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = GetResponseByUserAndSurveyUseCase(ResponseRepositoryImpl(db))
        response = await use_case.execute(current_user_id, survey_id)

        if not response:
            log_warning(f"Свой ответ на опрос {survey_id} не найден для пользователя {current_user_id}", service="survey-service")
            return None

        return ResponseOut(
            id=str(response.id),
            survey_id=str(response.survey_id),
            user_id=str(response.user_id),
            answers={str(k): v for k, v in response.answers.items()},
            submitted_at=response.submitted_at.isoformat() if response.submitted_at else None,
        )

    except Exception as e:
        log_error(f"Ошибка получения своего ответа на опрос {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/responses/me", response_model=List[ResponseOut])
async def get_my_all_responses(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение всех ответов пользователя {current_user_id}", service="survey-service")

    try:
        use_case = GetResponsesByUserUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(current_user_id)

        return [
            ResponseOut(
                id=str(r.id),
                survey_id=str(r.survey_id),
                user_id=str(r.user_id),
                answers={str(k): v for k, v in r.answers.items()},
                submitted_at=r.submitted_at.isoformat() if r.submitted_at else None,
            )
            for r in responses
        ]

    except Exception as e:
        log_error(f"Ошибка получения всех ответов пользователя {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{survey_id}/responses", response_model=ResponseOut, status_code=201)
async def create_response_in_survey(
    survey_id: UUID,
    payload: ResponseCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Создание ответа на опрос {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")

        existing = await GetResponseByUserAndSurveyUseCase(ResponseRepositoryImpl(db)).execute(current_user_id, survey_id)
        if existing:
            raise HTTPException(status_code=400, detail="Вы уже отвечали на этот опрос")

        response = Response(
            id=UUID(),
            survey_id=survey_id,
            user_id=current_user_id,
            answers={UUID(k): v for k, v in payload.answers.items()},
            submitted_at=datetime.utcnow(),
        )

        use_case = CreateResponseUseCase(ResponseRepositoryImpl(db))
        created = await use_case.execute(response)

        return ResponseOut(
            id=str(created.id),
            survey_id=str(created.survey_id),
            user_id=str(created.user_id),
            answers={str(k): v for k, v in created.answers.items()},
            submitted_at=created.submitted_at.isoformat() if created.submitted_at else None,
        )

    except ValueError as e:
        log_warning(f"Ошибка создания ответа на опрос {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Неожиданная ошибка создания ответа на опрос {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/responses/{response_id}/answers", response_model=ResponseOut)
async def update_response_answers(
    survey_id: UUID,
    response_id: UUID,
    payload: ResponseUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление ответов в записи {response_id} опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")

        use_case = UpdateResponseAnswersUseCase(ResponseRepositoryImpl(db))
        updated = await use_case.execute(response_id, {UUID(k): v for k, v in payload.answers.items()})

        if str(updated.user_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Это не ваш ответ")

        return ResponseOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            user_id=str(updated.user_id),
            answers={str(k): v for k, v in updated.answers.items()},
            submitted_at=updated.submitted_at.isoformat() if updated.submitted_at else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления ответов в записи {response_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{survey_id}/responses/{response_id}/submit")
async def submit_response(
    survey_id: UUID,
    response_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Отправка ответа {response_id} на опрос {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = MarkResponseSubmittedUseCase(ResponseRepositoryImpl(db))
        submitted_at = datetime.utcnow()
        updated = await use_case.execute(response_id, submitted_at)

        if str(updated.user_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Это не ваш ответ")

        return {"detail": "Ответ отправлен", "submitted_at": submitted_at.isoformat()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка отправки ответа {response_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{survey_id}/responses/{response_id}")
async def delete_response(
    survey_id: UUID,
    response_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление ответа {response_id} из опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = DeleteResponseUseCase(ResponseRepositoryImpl(db))
        await use_case.execute(response_id)

        return {"detail": "Ответ удалён"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления ответа {response_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/responses/me", response_model=List[ResponseOut])
async def get_my_responses(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение всех ответов текущего пользователя {current_user_id}", service="survey-service")

    try:
        use_case = GetResponsesByUserUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(current_user_id)

        return [
            ResponseOut(
                id=str(r.id),
                survey_id=str(r.survey_id),
                user_id=str(r.user_id),
                answers={str(k): v for k, v in r.answers.items()},
                submitted_at=r.submitted_at.isoformat() if r.submitted_at else None,
            )
            for r in responses
        ]

    except Exception as e:
        log_error(f"Ошибка получения всех ответов пользователя {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")