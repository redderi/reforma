from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, List
from reforma_survey.presentation.schemas.template_schema import (
    TemplateAddAsset,
    TemplateCreate,
    TemplateDescriptionUpdate,
    TemplateNameUpdate,
    TemplateOut,
    TemplateRemoveAsset,
)
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_survey.infrastructure.repositories.template_repository_impl import (
    TemplateRepositoryImpl,
)
from reforma_survey.application.template.get_template_by_id_use_case import (
    GetTemplateByIdUseCase,
)
from reforma_survey.application.template.get_templates_by_owner_use_case import (
    GetTemplatesByOwnerUseCase,
)
from reforma_survey.application.template.create_template_use_case import (
    CreateTemplateUseCase,
)
from reforma_survey.application.template.update_template_name_use_case import (
    UpdateTemplateNameUseCase,
)
from reforma_survey.application.template.update_template_description_use_case import (
    UpdateTemplateDescriptionUseCase,
)
from reforma_survey.application.template.update_template_survey_style_use_case import (
    UpdateTemplateSurveyStyleUseCase,
)
from reforma_survey.application.template.update_template_question_style_use_case import (
    UpdateTemplateQuestionStyleUseCase,
)
from reforma_survey.application.template.add_template_asset_use_case import (
    AddTemplateAssetUseCase,
)
from reforma_survey.application.template.remove_template_asset_use_case import (
    RemoveTemplateAssetUseCase,
)
from reforma_survey.application.template.delete_template_use_case import (
    DeleteTemplateUseCase,
)

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("/me", response_model=List[TemplateOut])
async def get_my_templates(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve current user's templates",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
    )

    try:
        use_case = GetTemplatesByOwnerUseCase(TemplateRepositoryImpl(db))
        templates = await use_case.execute(current_user_id)

        log_info(
            "User templates retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"templates_count": len(templates)},
        )

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
        log_error(
            "Unexpected error retrieving user templates",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(
    request: Request,
    template_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve template by ID",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"template_id": str(template_id)},
    )

    try:
        use_case = GetTemplateByIdUseCase(TemplateRepositoryImpl(db))
        template = await use_case.execute(template_id)

        if not template:
            log_warning(
                "Template not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=404, detail="Template not found")

        if str(template.owner_id) != str(current_user_id):
            log_warning(
                "User does not have access to template",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=403, detail="No access to template")

        log_info(
            "Template retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

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
        log_error(
            "Unexpected error retrieving template",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=TemplateOut, status_code=201)
async def create_template(
    request: Request,
    payload: TemplateCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Create template attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "name": payload.name,
            "description_length": len(payload.description)
            if payload.description
            else 0,
        },
    )

    try:
        use_case = CreateTemplateUseCase(TemplateRepositoryImpl(db))
        template_data = payload.dict(exclude_unset=True)
        created = await use_case.execute(template_data, current_user_id)

        log_info(
            "Template created successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(created.id)},
        )

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
        log_warning(
            "Template creation failed due to validation error",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"name": payload.name, "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error during template creation",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"name": payload.name, "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{template_id}/name", response_model=TemplateOut)
async def update_template_name(
    request: Request,
    template_id: UUID,
    payload: TemplateNameUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update template name attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"template_id": str(template_id), "new_name": payload.name},
    )

    try:
        use_case = UpdateTemplateNameUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.name)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update template name",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Template name updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

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
        log_warning(
            "Template name update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating template name",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{template_id}/description", response_model=TemplateOut)
async def update_template_description(
    request: Request,
    template_id: UUID,
    payload: TemplateDescriptionUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update template description attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "template_id": str(template_id),
            "new_description_length": len(payload.description)
            if payload.description
            else 0,
        },
    )

    try:
        use_case = UpdateTemplateDescriptionUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.description)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update template description",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Template description updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

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
        log_error(
            "Unexpected error updating template description",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{template_id}/survey-style", response_model=TemplateOut)
async def update_template_survey_style(
    request: Request,
    template_id: UUID,
    payload: Dict,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update template survey style attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"template_id": str(template_id), "style_keys": list(payload.keys())},
    )

    try:
        use_case = UpdateTemplateSurveyStyleUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update template survey style",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Template survey style updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

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
        log_error(
            "Unexpected error updating template survey style",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{template_id}/question-style", response_model=TemplateOut)
async def update_template_question_style(
    request: Request,
    template_id: UUID,
    payload: Dict,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update template question style attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"template_id": str(template_id), "style_keys": list(payload.keys())},
    )

    try:
        use_case = UpdateTemplateQuestionStyleUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update template question style",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Template question style updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

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
        log_error(
            "Unexpected error updating template question style",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{template_id}/assets")
async def add_template_asset(
    request: Request,
    template_id: UUID,
    payload: TemplateAddAsset,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Add template asset attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "template_id": str(template_id),
            "asset_url": payload.asset_url[:100] + "..."
            if len(payload.asset_url) > 100
            else payload.asset_url,
        },
    )

    try:
        use_case = AddTemplateAssetUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.asset_url)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to add asset to template",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Template asset added successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

        return {"detail": "Asset added", "assets": updated.assets}

    except ValueError as e:
        log_warning(
            "Add template asset failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error adding template asset",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{template_id}/assets")
async def remove_template_asset(
    request: Request,
    template_id: UUID,
    payload: TemplateRemoveAsset,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Remove template asset attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "template_id": str(template_id),
            "asset_url": payload.asset_url[:100] + "..."
            if len(payload.asset_url) > 100
            else payload.asset_url,
        },
    )

    try:
        use_case = RemoveTemplateAssetUseCase(TemplateRepositoryImpl(db))
        updated = await use_case.execute(template_id, payload.asset_url)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to remove asset from template",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"template_id": str(template_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Template asset removed successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

        return {"detail": "Asset removed", "assets": updated.assets}

    except ValueError as e:
        log_warning(
            "Remove template asset failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error removing template asset",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{template_id}")
async def delete_template(
    request: Request,
    template_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Delete template attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"template_id": str(template_id)},
    )

    try:
        use_case = DeleteTemplateUseCase(TemplateRepositoryImpl(db))
        await use_case.execute(template_id)

        log_info(
            "Template deleted successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id)},
        )

        return {"detail": "Template deleted"}

    except ValueError as e:
        log_warning(
            "Template deletion failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error deleting template",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"template_id": str(template_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
