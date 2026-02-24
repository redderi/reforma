# reforma_report/presentation/routers/survey_stats_router.py
from fastapi import APIRouter, Request, HTTPException, Depends
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_common.logger import log_info, log_error
from reforma_report.presentation.dependencies import get_current_user_id, get_db
from reforma_report.infrastructure.repositories.survey_stats_repository_impl import (
    SurveyStatsRepositoryImpl,
)
from reforma_report.application.add_allowed_user_use_case import AddAllowedUserUseCase
from reforma_report.application.check_user_access_use_case import CheckUserAccessUseCase
from reforma_report.application.remove_allowed_user_use_case import RemoveAllowedUserUseCase
from reforma_report.domain.entities.survey_stats import SurveyStats

router = APIRouter(prefix="/survey_stats", tags=["SurveyStatsAccess"])


# -----------------------
# Получение статистики опроса
# -----------------------
@router.get("/{survey_id}", response_model=SurveyStats | None)
async def get_survey_stats(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)
    log_info(
        "Retrieve survey stats",
        service="report_service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_id": str(survey_id)},
    )

    try:
        repository = SurveyStatsRepositoryImpl(db)
        access_use_case = CheckUserAccessUseCase(repository)

        has_access = await access_use_case.execute(survey_id, current_user_id)
        if not has_access:
            log_info(
                "User has no access to survey stats",
                service="report_service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="Access denied")

        stats = await repository.get(survey_id)
        return stats

    except Exception as e:
        log_error(
            "Unexpected error retrieving survey stats",
            service="report_service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


# -----------------------
# Управление доступом к опросу
# -----------------------
@router.post("/{survey_id}/allow/{user_id}")
async def add_allowed_user(
    request: Request,
    survey_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    try:
        repository = SurveyStatsRepositoryImpl(db)
        stats = await repository.get(survey_id)
        if not stats or stats.owner_id != current_user_id:
            raise HTTPException(status_code=403, detail="Only owner can grant access")

        use_case = AddAllowedUserUseCase(repository)
        await use_case.execute(survey_id, user_id)

        log_info(
            "Added allowed user for survey stats",
            service="report_service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "allowed_user_id": str(user_id)},
        )
        return {"detail": "User added to allowed list"}

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error adding allowed user to survey stats",
            service="report_service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{survey_id}/allow/{user_id}")
async def remove_allowed_user(
    request: Request,
    survey_id: UUID,
    user_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    try:
        repository = SurveyStatsRepositoryImpl(db)
        stats = await repository.get(survey_id)
        if not stats or stats.owner_id != current_user_id:
            raise HTTPException(status_code=403, detail="Only owner can remove access")

        use_case = RemoveAllowedUserUseCase(repository)
        await use_case.execute(survey_id, user_id)

        log_info(
            "Removed allowed user from survey stats",
            service="report_service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "removed_user_id": str(user_id)},
        )
        return {"detail": "User removed from allowed list"}

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error removing allowed user from survey stats",
            service="report_service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")