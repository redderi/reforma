from fastapi import APIRouter, Request, HTTPException, Depends
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_common.logger import log_info, log_error
from reforma_report.presentation.dependencies import get_current_user_id, get_db
from reforma_report.infrastructure.repositories.question_stats_repository_impl import (
    QuestionStatsRepositoryImpl,
)
from reforma_report.application.check_user_access_use_case import CheckUserAccessUseCase
from reforma_report.domain.entities.question_stats import QuestionStats

router = APIRouter(prefix="/question_stats", tags=["QuestionStats"])


@router.get("/{survey_stat_id}/{question_id}", response_model=QuestionStats | None)
async def get_question_stats(
    request: Request,
    survey_stat_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve question stats",
        service="report_service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"survey_stat_id": str(survey_stat_id), "question_id": str(question_id)},
    )

    try:
        repository = QuestionStatsRepositoryImpl(db)
        access_use_case = CheckUserAccessUseCase(repository)

        # Проверяем доступ через SurveyStats (только владелец или разрешённые пользователи)
        has_access = await access_use_case.execute(
            survey_stat_id, current_user_id
        )
        if not has_access:
            log_info(
                "User has no access to question stats",
                service="report_service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_stat_id": str(survey_stat_id), "question_id": str(question_id)},
            )
            raise HTTPException(status_code=403, detail="Access denied")

        stats = await repository.get(survey_stat_id, question_id)
        if not stats:
            log_info(
                "Question stats not found",
                service="report_service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_stat_id": str(survey_stat_id), "question_id": str(question_id)},
            )
            return None

        return stats

    except Exception as e:
        log_error(
            "Unexpected error retrieving question stats",
            service="report_service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_stat_id": str(survey_stat_id),
                "question_id": str(question_id),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/survey/{survey_stat_id}", response_model=list[QuestionStats])
async def list_question_stats_by_survey(
    request: Request,
    survey_stat_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    try:
        repository = QuestionStatsRepositoryImpl(db)
        access_use_case = CheckUserAccessUseCase(repository)

        # Проверка доступа через SurveyStats
        has_access = await access_use_case.execute(
            survey_stat_id, current_user_id
        )
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")

        stats_list = await repository.list_by_survey(survey_stat_id)
        return stats_list

    except Exception as e:
        log_error(
            "Unexpected error listing question stats by survey",
            service="report_service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_stat_id": str(survey_stat_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")