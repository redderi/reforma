from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID, uuid4
from typing import List
from reforma_survey.application.handlers.sentiment_request_handler import GetResponsesByQuestionUseCase
from reforma_survey.domain.entities.response import Response
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_survey.presentation.dependencies.get_event_publisher import get_event_publisher
from reforma_survey.presentation.schemas.response_schema import (
    ResponseOut,
    ResponseCreate,
    ResponseUpdate,
)
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_survey.presentation.dependencies.get_optional_user_id import (
    get_optional_user_id,
)
from reforma_survey.infrastructure.repositories.survey_repository_impl import (
    SurveyRepositoryImpl,
)
from reforma_survey.infrastructure.repositories.response_repository_impl import (
    ResponseRepositoryImpl,
)
from reforma_survey.application.response.get_responses_by_survey_use_case import (
    GetResponsesBySurveyUseCase,
)
from reforma_survey.application.response.get_response_by_user_and_survey_use_case import (
    GetResponseByUserAndSurveyUseCase,
)
from reforma_survey.application.response.get_latest_responses_by_user_use_case import (
    GetLatestResponsesByUserUseCase,
)
from reforma_survey.application.response.create_response_use_case import (
    CreateResponseUseCase,
)
from reforma_survey.application.response.update_response_answers_use_case import (
    UpdateResponseAnswersUseCase,
)
from reforma_survey.application.response.mark_response_submitted_use_case import (
    MarkResponseSubmittedUseCase,
)
from reforma_survey.application.response.delete_response_use_case import (
    DeleteResponseUseCase,
)
from reforma_survey.application.response.has_already_responded_use_case import (
    HasAlreadyRespondedUseCase,
)
from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Responses"])


def to_response_out(response: Response) -> ResponseOut:
    return ResponseOut(
        id=str(response.id),
        survey_id=str(response.survey_id),
        user_id=str(response.user_id) if response.user_id else None,
        anonymous_id=response.anonymous_id,
        answers={str(k): v for k, v in response.answers.items()},
        submitted_at=response.submitted_at.isoformat()
        if response.submitted_at
        else None,
    )


@router.get("/{survey_id}/responses", response_model=List[ResponseOut])
async def get_responses_in_survey(
    request: Request,
    survey_id: UUID,
    limit: int = 100,
    offset: int = 0,
    include_anonymous: bool = True,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve responses for survey",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "limit": limit,
            "offset": offset,
            "include_anonymous": include_anonymous,
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
                "User does not have access to survey responses",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No access to survey responses")

        use_case = GetResponsesBySurveyUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(
            survey_id=survey_id,
            limit=limit,
            offset=offset,
            include_anonymous=include_anonymous,
        )

        log_info(
            "Survey responses retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "responses_count": len(responses)},
        )

        return [to_response_out(r) for r in responses]

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving survey responses",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
    

@router.get("/{survey_id}/responses/question/{question_id}", response_model=List[ResponseOut])
async def get_responses_for_question(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    limit: int = 100,
    offset: int = 0,
    include_anonymous: bool = True,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)
    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey or str(survey.owner_id) != str(current_user_id):
            raise HTTPException(403, detail="No access to survey responses")

        use_case = GetResponsesByQuestionUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(
            survey_id=survey_id,
            question_id=question_id,
            limit=limit,
            offset=offset,
            include_anonymous=include_anonymous
        )

        return [to_response_out(r) for r in responses]

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving responses for question",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "question_id": str(question_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{survey_id}/responses/me", response_model=ResponseOut | None)
async def get_my_response_in_survey(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve my response for survey",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        use_case = GetResponseByUserAndSurveyUseCase(ResponseRepositoryImpl(db))
        response = await use_case.execute(
            survey_id=survey_id,
            user_id=current_user_id,
        )

        if not response:
            log_info(
                "No response found for current user in survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            return None

        log_info(
            "My response retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

        return to_response_out(response)

    except Exception as e:
        log_error(
            "Unexpected error retrieving my response",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/responses/me", response_model=List[ResponseOut])
async def get_my_responses(
    request: Request,
    limit: int = 20,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve latest responses for current user",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"limit": limit},
    )

    try:
        use_case = GetLatestResponsesByUserUseCase(ResponseRepositoryImpl(db))
        responses = await use_case.execute(user_id=current_user_id, limit=limit)

        log_info(
            "User latest responses retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"responses_count": len(responses)},
        )

        return [to_response_out(r) for r in responses]

    except Exception as e:
        log_error(
            "Unexpected error retrieving user latest responses",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{survey_id}/responses", response_model=ResponseOut, status_code=201)
async def create_response(
    request: Request,
    survey_id: UUID,
    payload: ResponseCreate,
    current_user_id: UUID | None = Depends(
        get_optional_user_id
    ),  # None для анонимов
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Create response attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id) if current_user_id else None,
        context={
            "survey_id": str(survey_id),
            "anonymous_id": payload.anonymous_id,
            "fingerprint": payload.fingerprint,
            "answers_count": len(payload.answers),
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
                user_id=str(current_user_id) if current_user_id else None,
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(404, "Survey not found")

        repo = ResponseRepositoryImpl(db)
        already = await repo.has_already_responded(
            survey_id=survey_id,
            user_id=current_user_id,
            anonymous_id=payload.anonymous_id,
            ip_address=request.client.host,
        )

        if already and survey.settings.get("block_repeated_responses", False):
            log_warning(
                "User has already responded to survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id) if current_user_id else None,
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(403, "You have already completed this survey")

        response = Response(
            id=uuid4(),
            survey_id=survey_id,
            user_id=current_user_id,
            anonymous_id=payload.anonymous_id,
            ip_address=request.client.host,
            fingerprint=payload.fingerprint,
            user_agent=request.headers.get("user-agent"),
            answers={UUID(k): v for k, v in payload.answers.items()},
            submitted_at=None,  # пока черновик
        )

        use_case = CreateResponseUseCase(repo)
        created = await use_case.execute(response)

        log_info(
            "Response created successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id) if current_user_id else None,
            context={"response_id": str(created.id)},
        )

        return to_response_out(created)

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error creating response",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id) if current_user_id else None,
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(500, "Internal server error")


@router.patch(
    "/{survey_id}/responses/{response_id}/answers", response_model=ResponseOut
)
async def update_response_answers(
    request: Request,
    survey_id: UUID,
    response_id: UUID,
    payload: ResponseUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update response answers attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "response_id": str(response_id),
            "new_answers_count": len(payload.answers),
        },
    )

    try:
        use_case = UpdateResponseAnswersUseCase(ResponseRepositoryImpl(db))
        updated = await use_case.execute(
            response_id=response_id,
            new_answers={UUID(k): v for k, v in payload.answers.items()},
        )

        if updated.user_id != current_user_id:
            log_warning(
                "User attempting to update another user's response",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "response_id": str(response_id),
                    "response_owner_id": str(updated.user_id),
                },
            )
            raise HTTPException(403, "This is not your response")

        log_info(
            "Response answers updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id)},
        )

        return to_response_out(updated)

    except ValueError as e:
        log_warning(
            "Response answers update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id), "error_detail": str(e)},
        )
        raise HTTPException(400, str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating response answers",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id), "error_detail": str(e)},
        )
        raise HTTPException(500, "Internal server error")


@router.post("/{survey_id}/responses/{response_id}/submit", response_model=ResponseOut)
async def submit_response(
    request: Request,
    survey_id: UUID,
    response_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Submit response attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "response_id": str(response_id)},
    )

    try:
        use_case = MarkResponseSubmittedUseCase(ResponseRepositoryImpl(db), event_publisher)
        updated = await use_case.execute(response_id=response_id)

        if updated.user_id != current_user_id:
            log_warning(
                "User attempting to submit another user's response",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "response_id": str(response_id),
                    "response_owner_id": str(updated.user_id),
                },
            )
            raise HTTPException(403, "This is not your response")

        log_info(
            "Response submitted successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id)},
        )

        return to_response_out(updated)

    except ValueError as e:
        log_warning(
            "Response submission failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id), "error_detail": str(e)},
        )
        raise HTTPException(400, str(e))

    except Exception as e:
        log_error(
            "Unexpected error submitting response",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id), "error_detail": str(e)},
        )
        raise HTTPException(500, "Internal server error")


@router.delete("/{survey_id}/responses/{response_id}")
async def delete_response(
    request: Request,
    survey_id: UUID,
    response_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Delete response attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "response_id": str(response_id)},
    )

    try:
        use_case = DeleteResponseUseCase(ResponseRepositoryImpl(db))
        await use_case.execute(response_id)

        log_info(
            "Response deleted successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id)},
        )

        return {"detail": "Response deleted"}

    except ValueError as e:
        log_warning(
            "Response deletion failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"response_id": str(response_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error deleting response",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(survey_id),
                "response_id": str(response_id),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")
