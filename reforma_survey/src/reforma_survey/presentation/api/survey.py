from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from reforma_survey.presentation.schemas.survey_schema import (
    AddQuestionRequest,
    ReorderQuestionsRequest,
    SurveyDescriptionUpdate,
    SurveyOut,
    SurveySettingsUpdate,
    SurveyTemplateUpdate,
    SurveyTitleUpdate,
    SurveyCreate,
)
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_survey.infrastructure.repositories.survey_repository_impl import (
    SurveyRepositoryImpl,
)
from reforma_survey.application.survey.get_survey_by_id_use_case import (
    GetSurveyByIdUseCase,
)
from reforma_survey.application.survey.get_surveys_by_owner_use_case import (
    GetSurveysByOwnerUseCase,
)
from reforma_survey.application.survey.get_published_surveys_use_case import (
    GetPublishedSurveysUseCase,
)
from reforma_survey.application.survey.create_survey_use_case import CreateSurveyUseCase
from reforma_survey.application.survey.update_survey_title_use_case import (
    UpdateSurveyTitleUseCase,
)
from reforma_survey.application.survey.update_survey_description_use_case import (
    UpdateSurveyDescriptionUseCase,
)
from reforma_survey.application.survey.update_survey_settings_use_case import (
    UpdateSurveySettingsUseCase,
)
from reforma_survey.application.survey.set_survey_template_use_case import (
    SetSurveyTemplateUseCase,
)
from reforma_survey.application.survey.publish_survey_use_case import (
    PublishSurveyUseCase,
)
from reforma_survey.application.survey.unpublish_survey_use_case import (
    UnpublishSurveyUseCase,
)
from reforma_survey.application.survey.delete_survey_use_case import DeleteSurveyUseCase
from reforma_survey.application.survey.add_question_to_survey_use_case import (
    AddQuestionToSurveyUseCase,
)
from reforma_survey.application.survey.remove_question_from_survey_use_case import (
    RemoveQuestionFromSurveyUseCase,
)
from reforma_survey.application.survey.reorder_survey_questions_use_case import (
    ReorderSurveyQuestionsUseCase,
)

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Surveys"])


@router.get("/me", response_model=List[SurveyOut])
async def get_my_surveys(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve current user's surveys",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
    )

    try:
        use_case = GetSurveysByOwnerUseCase(SurveyRepositoryImpl(db))
        surveys = await use_case.execute(current_user_id)

        log_info(
            "User surveys retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"surveys_count": len(surveys)},
        )

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
        log_error(
            "Unexpected error retrieving user surveys",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{survey_id}", response_model=SurveyOut)
async def get_survey(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve survey by ID",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        use_case = GetSurveyByIdUseCase(SurveyRepositoryImpl(db))
        survey = await use_case.execute(survey_id)

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

        log_info(
            "Survey retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

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
        log_error(
            "Unexpected error retrieving survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=SurveyOut, status_code=201)
async def create_survey(
    request: Request,
    payload: SurveyCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Create survey attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "title": payload.title,
            "description_length": len(payload.description)
            if payload.description
            else 0,
        },
    )

    try:
        use_case = CreateSurveyUseCase(SurveyRepositoryImpl(db))
        created = await use_case.execute(payload.dict(), current_user_id)

        log_info(
            "Survey created successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(created.id)},
        )

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
        log_warning(
            "Survey creation failed due to validation error",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"title": payload.title, "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error during survey creation",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"title": payload.title, "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/title", response_model=SurveyOut)
async def update_survey_title(
    request: Request,
    survey_id: UUID,
    payload: SurveyTitleUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update survey title attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "new_title_length": len(payload.title)},
    )

    try:
        use_case = UpdateSurveyTitleUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.title)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update survey title",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Survey title updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

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
        log_warning(
            "Survey title update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating survey title",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/description", response_model=SurveyOut)
async def update_survey_description(
    request: Request,
    survey_id: UUID,
    payload: SurveyDescriptionUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update survey description attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "new_description_length": len(payload.description)
            if payload.description
            else 0,
        },
    )

    try:
        use_case = UpdateSurveyDescriptionUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.description)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update survey description",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Survey description updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

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
        log_error(
            "Unexpected error updating survey description",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/settings", response_model=SurveyOut)
async def update_survey_settings(
    request: Request,
    survey_id: UUID,
    payload: SurveySettingsUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update survey settings attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        use_case = UpdateSurveySettingsUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.settings)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update survey settings",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Survey settings updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

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
        log_error(
            "Unexpected error updating survey settings",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/template", response_model=SurveyOut)
async def set_survey_template(
    request: Request,
    survey_id: UUID,
    payload: SurveyTemplateUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Set survey template attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "template_id": str(payload.template_id) if payload.template_id else None,
        },
    )

    try:
        use_case = SetSurveyTemplateUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.template_id)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to set survey template",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Survey template set successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

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
        log_error(
            "Unexpected error setting survey template",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{survey_id}/publish")
async def publish_survey(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Publish survey attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        use_case = PublishSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to publish survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Survey published successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

        return {"detail": "Survey published", "published": updated.published}

    except ValueError as e:
        log_warning(
            "Survey publish failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error publishing survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{survey_id}/unpublish")
async def unpublish_survey(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Unpublish survey attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        use_case = UnpublishSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to unpublish survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Survey unpublished successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

        return {"detail": "Survey unpublished", "published": updated.published}

    except ValueError as e:
        log_warning(
            "Survey unpublish failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error unpublishing survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{survey_id}")
async def delete_survey(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Delete survey attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        use_case = DeleteSurveyUseCase(SurveyRepositoryImpl(db))
        await use_case.execute(survey_id)

        log_info(
            "Survey deleted successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

        return {"detail": "Survey deleted"}

    except ValueError as e:
        log_warning(
            "Survey deletion failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error deleting survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{survey_id}/questions")
async def add_question_to_survey(
    request: Request,
    survey_id: UUID,
    payload: AddQuestionRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Add question to survey attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "question_id": str(payload.question_id)},
    )

    try:
        use_case = AddQuestionToSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.question_id)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to add question to survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Question added to survey successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(survey_id),
                "question_id": str(payload.question_id),
            },
        )

        return {
            "detail": "Question added",
            "questions": [str(q) for q in updated.questions],
        }

    except ValueError as e:
        log_warning(
            "Add question to survey failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error adding question to survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{survey_id}/questions/{question_id}")
async def remove_question_from_survey(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Remove question from survey attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id), "question_id": str(question_id)},
    )

    try:
        use_case = RemoveQuestionFromSurveyUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, question_id)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to remove question from survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Question removed from survey successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "question_id": str(question_id)},
        )

        return {
            "detail": "Question removed",
            "questions": [str(q) for q in updated.questions],
        }

    except ValueError as e:
        log_warning(
            "Remove question from survey failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error removing question from survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{survey_id}/reorder-questions")
async def reorder_survey_questions(
    request: Request,
    survey_id: UUID,
    payload: ReorderQuestionsRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Reorder survey questions attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "questions_count": len(payload.question_ids),
        },
    )

    try:
        use_case = ReorderSurveyQuestionsUseCase(SurveyRepositoryImpl(db))
        updated = await use_case.execute(survey_id, payload.question_ids)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to reorder survey questions",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Survey questions reordered successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id)},
        )

        return {
            "detail": "Questions order updated",
            "questions": [str(q) for q in updated.questions],
        }

    except ValueError as e:
        log_warning(
            "Survey questions reorder failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error reordering survey questions",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
