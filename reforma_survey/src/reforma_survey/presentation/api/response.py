from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from typing import List, Optional, Dict


from reforma_survey.domain.entities.response import Response
from reforma_survey.presentation.schemas.response_schema import ResponseOut, ResponseCreate, ResponseUpdate
from reforma_survey.presentation.dependencies import get_current_user_id, get_db, get_optional_user_id
from reforma_survey.infrastructure.repositories.survey_repository_impl import SurveyRepositoryImpl
from reforma_survey.infrastructure.repositories.response_repository_impl import ResponseRepositoryImpl

from reforma_survey.application.response.get_responses_by_survey_use_case import GetResponsesBySurveyUseCase
from reforma_survey.application.response.get_response_by_user_and_survey_use_case import GetResponseByUserAndSurveyUseCase
from reforma_survey.application.response.get_latest_responses_by_user_use_case import GetLatestResponsesByUserUseCase
from reforma_survey.application.response.create_response_use_case import CreateResponseUseCase
from reforma_survey.application.response.update_response_answers_use_case import UpdateResponseAnswersUseCase
from reforma_survey.application.response.mark_response_submitted_use_case import MarkResponseSubmittedUseCase
from reforma_survey.application.response.delete_response_use_case import DeleteResponseUseCase
from reforma_survey.application.response.has_already_responded_use_case import HasAlreadyRespondedUseCase

from reforma_common.logger import log_info, log_warning, log_error


router = APIRouter(prefix="/surveys", tags=["Responses"])


def to_response_out(response: Response) -> ResponseOut:
    return ResponseOut(
        id=str(response.id),
        survey_id=str(response.survey_id),
        user_id=str(response.user_id) if response.user_id else None,
        anonymous_id=response.anonymous_id,
        answers={str(k): v for k, v in response.answers.items()},
        submitted_at=response.submitted_at.isoformat() if response.submitted_at else None,
    )


@router.get("/{survey_id}/responses", response_model=List[ResponseOut])
async def get_responses_in_survey(
    survey_id: UUID,
    limit: int = 100,
    offset: int = 0,
    include_anonymous: bool = True,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение ответов опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)

        if not survey:
            raise HTTPException(404, "Опрос не найден")

        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(403, "Нет доступа к ответам этого опроса")

        use_case = GetResponsesBySurveyUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(
            survey_id=survey_id,
            limit=limit,
            offset=offset,
            include_anonymous=include_anonymous
        )

        return [to_response_out(r) for r in responses]

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения ответов опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(500, "Внутренняя ошибка")


@router.get("/{survey_id}/responses/me", response_model=Optional[ResponseOut])
async def get_my_response_in_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение своего ответа на опрос {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = GetResponseByUserAndSurveyUseCase(ResponseRepositoryImpl(db))
        response = await use_case.execute(
            survey_id=survey_id,
            user_id=current_user_id,
        )

        if not response:
            return None

        return to_response_out(response)

    except Exception as e:
        log_error(f"Ошибка получения своего ответа: {e}", service="survey-service")
        raise HTTPException(500, "Внутренняя ошибка")


@router.get("/responses/me", response_model=List[ResponseOut])
async def get_my_responses(
    limit: int = 20,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение последних ответов пользователя {current_user_id}", service="survey-service")

    try:
        use_case = GetLatestResponsesByUserUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(user_id=current_user_id, limit=limit)
        return [to_response_out(r) for r in responses]

    except Exception as e:
        log_error(f"Ошибка получения ответов пользователя: {e}", service="survey-service")
        raise HTTPException(500, "Внутренняя ошибка")


@router.post("/{survey_id}/responses", response_model=ResponseOut, status_code=201)
async def create_response(
    survey_id: UUID,
    payload: ResponseCreate,
    request: Request,
    current_user_id: Optional[UUID] = Depends(get_optional_user_id),  # None для анонимов
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Создание ответа на опрос {survey_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(404, "Опрос не найден")

        # Проверка на повторное прохождение
        repo = ResponseRepositoryImpl(db)
        already = await repo.has_already_responded(
            survey_id=survey_id,
            user_id=current_user_id,
            anonymous_id=payload.anonymous_id,
            ip_address=request.client.host
        )

        if already and survey.settings.get("block_repeated_responses", False):
            raise HTTPException(403, "Вы уже проходили этот опрос")

        response = Response(
            id=uuid4(),
            survey_id=survey_id,
            user_id=current_user_id,
            anonymous_id=payload.anonymous_id,
            ip_address=request.client.host,
            fingerprint=payload.fingerprint,
            user_agent=request.headers.get("user-agent"),
            answers={UUID(k): v for k, v in payload.answers.items()},
            submitted_at=None  # пока черновик
        )

        use_case = CreateResponseUseCase(repo)
        created = await use_case.execute(response)

        return to_response_out(created)

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка создания ответа: {e}", service="survey-service")
        raise HTTPException(500, "Внутренняя ошибка")


@router.patch("/{survey_id}/responses/{response_id}/answers", response_model=ResponseOut)
async def update_response_answers(
    survey_id: UUID,
    response_id: UUID,
    payload: ResponseUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление ответов в {response_id}", service="survey-service")

    try:
        use_case = UpdateResponseAnswersUseCase(ResponseRepositoryImpl(db))
        updated = await use_case.execute(
            response_id=response_id,
            new_answers={UUID(k): v for k, v in payload.answers.items()}
        )

        if updated.user_id != current_user_id:
            raise HTTPException(403, "Это не ваш ответ")

        return to_response_out(updated)

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log_error(f"Ошибка обновления ответов: {e}", service="survey-service")
        raise HTTPException(500, "Внутренняя ошибка")


@router.post("/{survey_id}/responses/{response_id}/submit", response_model=ResponseOut)
async def submit_response(
    survey_id: UUID,
    response_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Отправка ответа {response_id}", service="survey-service")

    try:
        use_case = MarkResponseSubmittedUseCase(ResponseRepositoryImpl(db))
        updated = await use_case.execute(response_id=response_id)

        if updated.user_id != current_user_id:
            raise HTTPException(403, "Это не ваш ответ")

        return to_response_out(updated)

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log_error(f"Ошибка отправки ответа: {e}", service="survey-service")
        raise HTTPException(500, "Внутренняя ошибка")


@router.delete("/{survey_id}/responses/{response_id}")
async def delete_response(
    survey_id: UUID,
    response_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление ответа {response_id}", service="survey-service")

    try:
        use_case = DeleteResponseUseCase(ResponseRepositoryImpl(db))
        await use_case.execute(response_id)

        return {"detail": "Ответ удалён"}

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log_error(f"Ошибка удаления ответа: {e}", service="survey-service")
        raise HTTPException(500, "Внутренняя ошибка")