from fastapi import APIRouter, Depends, HTTPException
from reforma_survey.presentation.schemas.question_schema import QuestionCreate, QuestionOptionsUpdate, QuestionOrderUpdate, QuestionOut, QuestionStyleUpdate, QuestionTextUpdate, QuestionTypeUpdate
from reforma_survey.domain.entities.question import Question
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List


from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_survey.infrastructure.repositories.survey_repository_impl import SurveyRepositoryImpl
from reforma_survey.infrastructure.repositories.question_repository_impl import QuestionRepositoryImpl

from reforma_survey.application.question.get_question_by_id_use_case import GetQuestionByIdUseCase
from reforma_survey.application.question.get_question_by_survey_use_case import GetQuestionsBySurveyUseCase
from reforma_survey.application.question.get_ordered_questions_by_survey_use_case import GetOrderedQuestionsBySurveyUseCase
from reforma_survey.application.question.create_question_use_case import CreateQuestionUseCase
from reforma_survey.application.question.update_question_text_use_case import UpdateQuestionTextUseCase
from reforma_survey.application.question.update_question_type_use_case import UpdateQuestionTypeUseCase
from reforma_survey.application.question.update_question_options_use_case import UpdateQuestionOptionsUseCase
from reforma_survey.application.question.update_question_style_use_case import UpdateQuestionStyleUseCase
from reforma_survey.application.question.updare_question_order_use_case import UpdateQuestionOrderUseCase
from reforma_survey.application.question.delete_question_use_case import DeleteQuestionUseCase
from reforma_survey.application.question.question_exists_use_case import QuestionExistsUseCase
from reforma_survey.application.question.count_questions_by_survey_use_case import CountQuestionsBySurveyUseCase

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Questions"])

@router.get("/{survey_id}/questions", response_model=List[QuestionOut])
async def get_questions_in_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение вопросов опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к опросу")

        use_case = GetQuestionsBySurveyUseCase(QuestionRepositoryImpl(db))
        questions = await use_case.execute(survey_id)

        return [
            QuestionOut(
                id=str(q.id),
                survey_id=str(q.survey_id),
                text=q.text,
                type=q.type,
                options=q.options,
                style=q.style,
                order=q.order,
                next_questions={k: str(v) for k, v in q.next_questions.items()},
            )
            for q in questions
        ]

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения вопросов опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/{survey_id}/questions/{question_id}", response_model=QuestionOut)
async def get_question_in_survey(
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение вопроса {question_id} в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа")

        use_case = GetQuestionByIdUseCase(QuestionRepositoryImpl(db))
        question = await use_case.execute(question_id)

        if not question:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        if question.survey_id != survey_id:
            raise HTTPException(status_code=404, detail="Вопрос не принадлежит этому опросу")

        return QuestionOut(
            id=str(question.id),
            survey_id=str(question.survey_id),
            text=question.text,
            type=question.type,
            options=question.options,
            style=question.style,
            order=question.order,
            next_questions={k: str(v) for k, v in question.next_questions.items()},
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{survey_id}/questions", response_model=QuestionOut, status_code=201)
async def create_question_in_survey(
    survey_id: UUID,
    payload: QuestionCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Создание вопроса в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав на создание вопроса")

        question = Question(
            id=UUID(),
            survey_id=survey_id,
            text=payload.text.strip(),
            type=payload.type.strip(),
            options=payload.options or [],
            style=payload.style or {},
            order=payload.order,
            next_questions={},
        )

        use_case = CreateQuestionUseCase(QuestionRepositoryImpl(db))
        created = await use_case.execute(question)

        return QuestionOut(
            id=str(created.id),
            survey_id=str(created.survey_id),
            text=created.text,
            type=created.type,
            options=created.options,
            style=created.style,
            order=created.order,
            next_questions={k: str(v) for k, v in created.next_questions.items()},
        )

    except ValueError as e:
        log_warning(f"Ошибка создания вопроса в опросе {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Неожиданная ошибка создания вопроса в опросе {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/text", response_model=QuestionOut)
async def update_question_text(
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionTextUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление текста вопроса {question_id} в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = UpdateQuestionTextUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.text)

        if updated.survey_id != survey_id:
            raise HTTPException(status_code=404, detail="Вопрос не принадлежит этому опросу")

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
            next_questions={k: str(v) for k, v in updated.next_questions.items()},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления текста вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/type", response_model=QuestionOut)
async def update_question_type(
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionTypeUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление типа вопроса {question_id} в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = UpdateQuestionTypeUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.type)

        if updated.survey_id != survey_id:
            raise HTTPException(status_code=404, detail="Вопрос не принадлежит этому опросу")

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
            next_questions={k: str(v) for k, v in updated.next_questions.items()},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления типа вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/options", response_model=QuestionOut)
async def update_question_options(
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionOptionsUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление вариантов ответа вопроса {question_id} в опросе {survey_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = UpdateQuestionOptionsUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.options)

        if updated.survey_id != survey_id:
            raise HTTPException(status_code=404, detail="Вопрос не принадлежит этому опросу")

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
            next_questions={k: str(v) for k, v in updated.next_questions.items()},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления вариантов ответа вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/style", response_model=QuestionOut)
async def update_question_style(
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionStyleUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление стиля вопроса {question_id} в опросе {survey_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = UpdateQuestionStyleUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.style)

        if updated.survey_id != survey_id:
            raise HTTPException(status_code=404, detail="Вопрос не принадлежит этому опросу")

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
            next_questions={k: str(v) for k, v in updated.next_questions.items()},
        )

    except Exception as e:
        log_error(f"Ошибка обновления стиля вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/order", response_model=QuestionOut)
async def update_question_order(
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionOrderUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление позиции вопроса {question_id} в опросе {survey_id} на {payload.order}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = UpdateQuestionOrderUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.order)

        if updated.survey_id != survey_id:
            raise HTTPException(status_code=404, detail="Вопрос не принадлежит этому опросу")

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
            next_questions={k: str(v) for k, v in updated.next_questions.items()},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления позиции вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{survey_id}/questions/{question_id}")
async def delete_question(
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление вопроса {question_id} из опроса {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = DeleteQuestionUseCase(QuestionRepositoryImpl(db))
        await use_case.execute(question_id)

        return {"detail": "Вопрос удалён"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления вопроса {question_id} из опроса {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")