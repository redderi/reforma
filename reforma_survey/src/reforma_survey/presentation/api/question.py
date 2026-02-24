from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID, uuid4
from typing import List

from reforma_survey.application.question.get_next_order_use_case import GetNextOrderUseCase
from reforma_survey.application.question.move_question_use_case import MoveQuestionUseCase
from reforma_survey.application.question.updare_question_order_use_case import UpdateQuestionOrderUseCase
from reforma_survey.presentation.schemas.question_schema import (
    QuestionCreate,
    QuestionOptionsUpdate,
    QuestionOrderUpdate,
    QuestionOut,
    QuestionStyleUpdate,
    QuestionTextUpdate,
    QuestionTypeUpdate,
)
from reforma_survey.domain.entities.question import Question
from sqlalchemy.ext.asyncio import AsyncSession

from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_survey.infrastructure.repositories.survey_repository_impl import (
    SurveyRepositoryImpl,
)
from reforma_survey.infrastructure.repositories.question_repository_impl import (
    QuestionRepositoryImpl,
)

from reforma_survey.application.question.get_question_by_id_use_case import (
    GetQuestionByIdUseCase,
)
from reforma_survey.application.question.get_question_by_survey_use_case import (
    GetQuestionsBySurveyUseCase,
)
from reforma_survey.application.question.get_ordered_questions_by_survey_use_case import (
    GetOrderedQuestionsBySurveyUseCase,
)
from reforma_survey.application.question.create_question_use_case import (
    CreateQuestionUseCase,
)
from reforma_survey.application.question.update_question_text_use_case import (
    UpdateQuestionTextUseCase,
)
from reforma_survey.application.question.update_question_type_use_case import (
    UpdateQuestionTypeUseCase,
)
from reforma_survey.application.question.update_question_options_use_case import (
    UpdateQuestionOptionsUseCase,
)
from reforma_survey.application.question.update_question_style_use_case import (
    UpdateQuestionStyleUseCase,
)
from reforma_survey.application.question.delete_question_use_case import (
    DeleteQuestionUseCase,
)
from reforma_survey.application.question.question_exists_use_case import (
    QuestionExistsUseCase,
)
from reforma_survey.application.question.count_questions_by_survey_use_case import (
    CountQuestionsBySurveyUseCase,
)

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Questions"])


@router.get("/{survey_id}/questions", response_model=List[QuestionOut])
async def get_questions_in_survey(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve questions for survey",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have access to survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No access to survey")

        use_case = GetQuestionsBySurveyUseCase(QuestionRepositoryImpl(db))
        questions = await use_case.execute(survey_id)

        log_info(
            "Questions retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "questions_count": len(questions)},
        )

        return [
            QuestionOut(
                id=str(q.id),
                survey_id=str(q.survey_id),
                text=q.text,
                type=q.type,
                options=q.options,
                style=q.style,
                order=q.order,
            )
            for q in questions
        ]

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving questions for survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{survey_id}/questions/{question_id}", response_model=QuestionOut)
async def get_question_in_survey(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve specific question in survey",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "question_id": str(question_id)},
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have access to survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No access")

        use_case = GetQuestionByIdUseCase(QuestionRepositoryImpl(db))
        question = await use_case.execute(question_id)

        if not question:
            log_warning(
                "Question not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"question_id": str(question_id)},
            )
            raise HTTPException(status_code=404, detail="Question not found")

        if question.survey_id != survey_id:
            log_warning(
                "Question does not belong to this survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "question_id": str(question_id),
                    "expected_survey_id": str(survey_id),
                },
            )
            raise HTTPException(
                status_code=404, detail="Question does not belong to this survey"
            )

        log_info(
            "Question retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return QuestionOut(
            id=str(question.id),
            survey_id=str(question.survey_id),
            text=question.text,
            type=question.type,
            options=question.options,
            style=question.style,
            order=question.order,
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving question",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(survey_id),
                "question_id": str(question_id),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{survey_id}/create_question", response_model=QuestionOut, status_code=201)
async def create_question_in_survey(
    request: Request,
    survey_id: UUID,
    payload: QuestionCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Create question in survey attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "text": payload.text[:100] + "..." if len(payload.text) > 100 else payload.text,
            "type": payload.type,
        },
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to create question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission to create question")

        question_repo = QuestionRepositoryImpl(db)
        use_case = CreateQuestionUseCase(question_repo)

        question = Question(
            id=uuid4(),
            survey_id=survey_id,
            text=payload.text.strip(),
            type=payload.type.strip(),
            options=payload.options or [],
            style=payload.style or {},
        )

        created = await use_case.execute(question) 

        log_info(
            "Question created successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(created.id)},
        )

        return QuestionOut(
            id=str(created.id),
            survey_id=str(created.survey_id),
            text=created.text,
            type=created.type,
            options=created.options,
            style=created.style,
            order=created.order,  # уже с корректным order
        )

    except ValueError as e:
        log_warning(
            "Question creation failed due to validation error",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error during question creation",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/questions/{question_id}/text", response_model=QuestionOut)
async def update_question_text(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionTextUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update question text attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "new_text_length": len(payload.text),
        },
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = UpdateQuestionTextUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.text)

        if updated.survey_id != survey_id:
            log_warning(
                "Question does not belong to this survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "question_id": str(question_id),
                    "expected_survey_id": str(survey_id),
                },
            )
            raise HTTPException(
                status_code=404, detail="Question does not belong to this survey"
            )

        log_info(
            "Question text updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
        )

    except ValueError as e:
        log_warning(
            "Question text update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating question text",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/questions/{question_id}/type", response_model=QuestionOut)
async def update_question_type(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionTypeUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update question type attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "new_type": payload.type,
        },
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = UpdateQuestionTypeUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.type)

        if updated.survey_id != survey_id:
            log_warning(
                "Question does not belong to this survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "question_id": str(question_id),
                    "expected_survey_id": str(survey_id),
                },
            )
            raise HTTPException(
                status_code=404, detail="Question does not belong to this survey"
            )

        log_info(
            "Question type updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
        )

    except ValueError as e:
        log_warning(
            "Question type update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating question type",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/{survey_id}/questions/{question_id}/options", response_model=QuestionOut
)
async def update_question_options(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionOptionsUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update question options attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "options_count": len(payload.options) if payload.options else 0,
        },
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = UpdateQuestionOptionsUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.options)

        if updated.survey_id != survey_id:
            log_warning(
                "Question does not belong to this survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "question_id": str(question_id),
                    "expected_survey_id": str(survey_id),
                },
            )
            raise HTTPException(
                status_code=404, detail="Question does not belong to this survey"
            )

        log_info(
            "Question options updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
        )

    except ValueError as e:
        log_warning(
            "Question options update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating question options",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/questions/{question_id}/style", response_model=QuestionOut)
async def update_question_style(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionStyleUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update question style attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "style_keys": list(payload.style.keys()) if payload.style else [],
        },
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = UpdateQuestionStyleUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.style)

        if updated.survey_id != survey_id:
            log_warning(
                "Question does not belong to this survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "question_id": str(question_id),
                    "expected_survey_id": str(survey_id),
                },
            )
            raise HTTPException(
                status_code=404, detail="Question does not belong to this survey"
            )

        log_info(
            "Question style updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
        )

    except Exception as e:
        log_error(
            "Unexpected error updating question style",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/questions/{question_id}/order", response_model=QuestionOut)
async def update_question_order(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    payload: QuestionOrderUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update question order attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "new_order": payload.order,
        },
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = UpdateQuestionOrderUseCase(QuestionRepositoryImpl(db))
        updated = await use_case.execute(question_id, payload.order)

        if updated.survey_id != survey_id:
            log_warning(
                "Question does not belong to this survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "question_id": str(question_id),
                    "expected_survey_id": str(survey_id),
                },
            )
            raise HTTPException(
                status_code=404, detail="Question does not belong to this survey"
            )

        log_info(
            "Question order updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return QuestionOut(
            id=str(updated.id),
            survey_id=str(updated.survey_id),
            text=updated.text,
            type=updated.type,
            options=updated.options,
            style=updated.style,
            order=updated.order,
        )

    except ValueError as e:
        log_warning(
            "Question order update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating question order",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{survey_id}/questions/{question_id}/delete")
async def delete_question(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Delete question attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "question_id": str(question_id)},
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to delete question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = DeleteQuestionUseCase(QuestionRepositoryImpl(db))
        await use_case.execute(question_id, survey_id)

        log_info(
            "Question deleted successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return {"detail": "Question deleted"}

    except ValueError as e:
        log_warning(
            "Question deletion failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error deleting question",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(survey_id),
                "question_id": str(question_id),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.patch("/{survey_id}/questions/{question_id}/move")
async def move_question(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    payload: dict,  # {"new_order": 2}
    db: AsyncSession = Depends(get_db),
    current_user_id = Depends(get_current_user_id)
):
    new_order = payload.get("new_order")
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Move question attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "question_id": str(question_id)},
    )

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            log_warning(
                "Survey not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=404, detail="Survey not found")

        if str(survey.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to move question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = MoveQuestionUseCase(QuestionRepositoryImpl(db))
        await use_case.execute(question_id, survey_id, new_order)

        log_info(
            "Question moved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id)},
        )

        return {"detail": "Question moved"}

    except ValueError as e:
        log_warning(
            "Question deletion failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error deleting question",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(survey_id),
                "question_id": str(question_id),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")