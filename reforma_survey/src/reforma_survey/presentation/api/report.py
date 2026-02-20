from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from reforma_survey.presentation.schemas.report_schema import (
    ReportFileUrlAdd,
    ReportFileUrlsSet,
    ReportOut,
    ReportRequest,
    ReportStatusUpdate,
)
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_survey.infrastructure.repositories.report_repository_impl import (
    ReportRepositoryImpl,
)
from reforma_survey.infrastructure.repositories.survey_repository_impl import (
    SurveyRepositoryImpl,
)
from reforma_survey.application.report.request_report_generation_use_case import (
    RequestReportGenerationUseCase,
)
from reforma_survey.application.report.get_report_by_id_use_case import (
    GetReportByIdUseCase,
)
from reforma_survey.application.report.get_reports_by_survey_use_case import (
    GetReportsBySurveyUseCase,
)
from reforma_survey.application.report.get_reports_by_owner_use_case import (
    GetReportsByOwnerUseCase,
)
from reforma_survey.application.report.update_report_status_use_case import (
    UpdateReportStatusUseCase,
)
from reforma_survey.application.report.add_report_file_url_use_case import (
    AddReportFileUrlUseCase,
)
from reforma_survey.application.report.set_report_file_urls_use_case import (
    SetReportFileUrlsUseCase,
)
from reforma_survey.application.report.delete_report_use_case import DeleteReportUseCase
from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/reports", tags=["Reports"])

event_publisher = EventPublisher()


@router.post("/", response_model=ReportOut, status_code=201)
async def request_report_generation(
    request: Request,
    payload: ReportRequest = Body(...),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Request report generation attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(payload.survey_id),
            "report_type": payload.report_type,
        },
    )

    try:
        use_case = RequestReportGenerationUseCase(
            report_repo=ReportRepositoryImpl(db),
            survey_repo=SurveyRepositoryImpl(db),
            event_publisher=event_publisher,  # или через DI / singleton
        )

        report = await use_case.execute(
            survey_id=payload.survey_id,
            owner_id=current_user_id,
            report_type=payload.report_type,
        )

        log_info(
            "Report generation requested successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "report_id": str(report.id),
                "survey_id": str(report.survey_id),
                "report_type": report.report_type,
            },
        )

        return ReportOut(
            id=str(report.id),
            survey_id=str(report.survey_id),
            owner_id=str(report.owner_id),
            requested_at=report.requested_at.isoformat(),
            status=report.status,
            report_type=report.report_type,
            processing_started_at=(
                report.processing_started_at.isoformat()
                if report.processing_started_at
                else None
            ),
            completed_at=report.completed_at.isoformat()
            if report.completed_at
            else None,
            file_urls=report.file_urls,
            error_message=report.error_message,
        )

    except ValueError as ve:
        log_warning(
            "Report generation request validation error",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(payload.survey_id),
                "report_type": payload.report_type,
                "error_detail": str(ve),
            },
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        log_error(
            "Unexpected error requesting report generation",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(payload.survey_id),
                "report_type": payload.report_type,
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    request: Request,
    report_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve report by ID request",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"report_id": str(report_id)},
    )

    try:
        use_case = GetReportByIdUseCase(ReportRepositoryImpl(db))
        report = await use_case.execute(report_id)

        if not report:
            log_warning(
                "Report not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"report_id": str(report_id)},
            )
            raise HTTPException(status_code=404, detail="Report not found")

        if str(report.owner_id) != str(current_user_id):
            log_warning(
                "User does not have access to report",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"report_id": str(report_id)},
            )
            raise HTTPException(status_code=403, detail="No access to this report")

        log_info(
            "Report retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id)},
        )

        return ReportOut(
            id=str(report.id),
            survey_id=str(report.survey_id),
            owner_id=str(report.owner_id),
            requested_at=report.requested_at.isoformat(),
            status=report.status,
            report_type=report.report_type,
            processing_started_at=report.processing_started_at.isoformat()
            if report.processing_started_at
            else None,
            completed_at=report.completed_at.isoformat()
            if report.completed_at
            else None,
            file_urls=report.file_urls,
            error_message=report.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving report",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/survey/{survey_id}", response_model=List[ReportOut])
async def get_reports_by_survey(
    request: Request,
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve reports for survey",
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
                "User does not have access to survey reports",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(
                status_code=403, detail="No access to reports of this survey"
            )

        use_case = GetReportsBySurveyUseCase(ReportRepositoryImpl(db))
        reports = await use_case.execute(survey_id)

        log_info(
            "Reports for survey retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "reports_count": len(reports)},
        )

        return [
            ReportOut(
                id=str(r.id),
                survey_id=str(r.survey_id),
                owner_id=str(r.owner_id),
                requested_at=r.requested_at.isoformat(),
                status=r.status,
                report_type=r.report_type,
                processing_started_at=r.processing_started_at.isoformat()
                if r.processing_started_at
                else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                file_urls=r.file_urls,
                error_message=r.error_message,
            )
            for r in reports
        ]

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving reports for survey",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=List[ReportOut])
async def get_my_reports(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve all reports for current user",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
    )

    try:
        use_case = GetReportsByOwnerUseCase(ReportRepositoryImpl(db))
        reports = await use_case.execute(current_user_id)

        log_info(
            "User reports retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"reports_count": len(reports)},
        )

        return [
            ReportOut(
                id=str(r.id),
                survey_id=str(r.survey_id),
                owner_id=str(r.owner_id),
                requested_at=r.requested_at.isoformat(),
                status=r.status,
                report_type=r.report_type,
                processing_started_at=r.processing_started_at.isoformat()
                if r.processing_started_at
                else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                file_urls=r.file_urls,
                error_message=r.error_message,
            )
            for r in reports
        ]

    except Exception as e:
        log_error(
            "Unexpected error retrieving user reports",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{report_id}/status")
async def update_report_status(
    request: Request,
    report_id: UUID,
    payload: ReportStatusUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update report status attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"report_id": str(report_id)},
    )

    try:
        use_case = UpdateReportStatusUseCase(ReportRepositoryImpl(db))
        updated = await use_case.execute(
            report_id,
            payload.status,
            datetime.fromisoformat(payload.processing_started_at)
            if payload.processing_started_at
            else None,
            datetime.fromisoformat(payload.completed_at)
            if payload.completed_at
            else None,
            payload.error_message,
        )

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to update report status",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"report_id": str(report_id)},
            )
            raise HTTPException(
                status_code=403, detail="No permission to update this report"
            )

        log_info(
            "Report status updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id)},
        )

        return {
            "detail": "Status updated",
            "status": updated.status,
            "completed_at": updated.completed_at.isoformat()
            if updated.completed_at
            else None,
        }

    except ValueError as e:
        log_warning(
            "Report status update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating report status",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{report_id}/file-url")
async def add_report_file_url(
    request: Request,
    report_id: UUID,
    payload: ReportFileUrlAdd,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Add report file URL attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "report_id": str(report_id),
            "file_url": payload.file_url[:100] + "..."
            if len(payload.file_url) > 100
            else payload.file_url,
        },
    )

    try:
        use_case = AddReportFileUrlUseCase(ReportRepositoryImpl(db))
        updated = await use_case.execute(report_id, payload.file_url)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to add file to report",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"report_id": str(report_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Report file URL added successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id)},
        )

        return {"detail": "File URL added", "file_urls": updated.file_urls}

    except ValueError as e:
        log_warning(
            "Add report file URL failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error adding report file URL",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{report_id}/file-urls")
async def set_report_file_urls(
    request: Request,
    report_id: UUID,
    payload: ReportFileUrlsSet,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Set report file URLs attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "report_id": str(report_id),
            "file_urls_count": len(payload.file_urls),
        },
    )

    try:
        use_case = SetReportFileUrlsUseCase(ReportRepositoryImpl(db))
        updated = await use_case.execute(report_id, payload.file_urls)

        if str(updated.owner_id) != str(current_user_id):
            log_warning(
                "User does not have permission to set file URLs for report",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"report_id": str(report_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        log_info(
            "Report file URLs set successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id)},
        )

        return {"detail": "File URLs updated", "file_urls": updated.file_urls}

    except ValueError as e:
        log_warning(
            "Set report file URLs failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error setting report file URLs",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{report_id}")
async def delete_report(
    request: Request,
    report_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Delete report attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={"report_id": str(report_id)},
    )

    try:
        use_case = DeleteReportUseCase(ReportRepositoryImpl(db))
        await use_case.execute(report_id)

        log_info(
            "Report deleted successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id)},
        )

        return {"detail": "Report deleted"}

    except ValueError as e:
        log_warning(
            "Report deletion failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error deleting report",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"report_id": str(report_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
