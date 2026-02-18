from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from reforma_survey.presentation.schemas.report_schema import ReportFileUrlAdd, ReportFileUrlsSet, ReportOut, ReportRequest, ReportStatusUpdate
from reforma_survey.infrastructure.rabbitmq.publisher import EventPublisher
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_survey.infrastructure.repositories.report_repository_impl import ReportRepositoryImpl
from reforma_survey.infrastructure.repositories.survey_repository_impl import SurveyRepositoryImpl

from reforma_survey.application.report.request_report_generation_use_case import RequestReportGenerationUseCase
from reforma_survey.application.report.get_report_by_id_use_case import GetReportByIdUseCase
from reforma_survey.application.report.get_reports_by_survey_use_case import GetReportsBySurveyUseCase
from reforma_survey.application.report.get_reports_by_owner_use_case import GetReportsByOwnerUseCase
from reforma_survey.application.report.update_report_status_use_case import UpdateReportStatusUseCase
from reforma_survey.application.report.add_report_file_url_use_case import AddReportFileUrlUseCase
from reforma_survey.application.report.set_report_file_urls_use_case import SetReportFileUrlsUseCase
from reforma_survey.application.report.delete_report_use_case import DeleteReportUseCase

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/reports", tags=["Reports"])

event_publisher = EventPublisher()

@router.post("/", response_model=ReportOut, status_code=201)
async def request_report_generation(
    payload: ReportRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Запрос генерации отчёта по опросу {payload.survey_id} от пользователя {current_user_id}", service="survey-service")

    try:
        use_case = RequestReportGenerationUseCase(
            report_repo=ReportRepositoryImpl(db),
            survey_repo=SurveyRepositoryImpl(db),
            event_publisher= event_publisher  # или через DI
        )
        report = await use_case.execute(payload.survey_id, current_user_id, payload.report_type)

        return ReportOut(
            id=str(report.id),
            survey_id=str(report.survey_id),
            owner_id=str(report.owner_id),
            requested_at=report.requested_at.isoformat(),
            status=report.status,
            report_type=report.report_type,
            processing_started_at=report.processing_started_at.isoformat() if report.processing_started_at else None,
            completed_at=report.completed_at.isoformat() if report.completed_at else None,
            file_urls=report.file_urls,
            error_message=report.error_message,
        )

    except ValueError as e:
        log_warning(f"Ошибка запроса отчёта по опросу {payload.survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Неожиданная ошибка запроса отчёта по опросу {payload.survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение отчёта {report_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = GetReportByIdUseCase(ReportRepositoryImpl(db))
        report = await use_case.execute(report_id)

        if not report:
            raise HTTPException(status_code=404, detail="Отчёт не найден")

        if str(report.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к этому отчёту")

        return ReportOut(
            id=str(report.id),
            survey_id=str(report.survey_id),
            owner_id=str(report.owner_id),
            requested_at=report.requested_at.isoformat(),
            status=report.status,
            report_type=report.report_type,
            processing_started_at=report.processing_started_at.isoformat() if report.processing_started_at else None,
            completed_at=report.completed_at.isoformat() if report.completed_at else None,
            file_urls=report.file_urls,
            error_message=report.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения отчёта {report_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/survey/{survey_id}", response_model=List[ReportOut])
async def get_reports_by_survey(
    survey_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение отчётов по опросу {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        # Проверяем опрос и права
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к отчётам этого опроса")

        use_case = GetReportsBySurveyUseCase(ReportRepositoryImpl(db))
        reports = await use_case.execute(survey_id)

        return [
            ReportOut(
                id=str(r.id),
                survey_id=str(r.survey_id),
                owner_id=str(r.owner_id),
                requested_at=r.requested_at.isoformat(),
                status=r.status,
                report_type=r.report_type,
                processing_started_at=r.processing_started_at.isoformat() if r.processing_started_at else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                file_urls=r.file_urls,
                error_message=r.error_message,
            )
            for r in reports
        ]

    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Ошибка получения отчётов по опросу {survey_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/me", response_model=List[ReportOut])
async def get_my_reports(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение всех отчётов пользователя {current_user_id}", service="survey-service")

    try:
        use_case = GetReportsByOwnerUseCase(ReportRepositoryImpl(db))
        reports = await use_case.execute(current_user_id)

        return [
            ReportOut(
                id=str(r.id),
                survey_id=str(r.survey_id),
                owner_id=str(r.owner_id),
                requested_at=r.requested_at.isoformat(),
                status=r.status,
                report_type=r.report_type,
                processing_started_at=r.processing_started_at.isoformat() if r.processing_started_at else None,
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                file_urls=r.file_urls,
                error_message=r.error_message,
            )
            for r in reports
        ]

    except Exception as e:
        log_error(f"Ошибка получения отчётов пользователя {current_user_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{report_id}/status")
async def update_report_status(
    report_id: UUID,
    payload: ReportStatusUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление статуса отчёта {report_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = UpdateReportStatusUseCase(ReportRepositoryImpl(db))
        updated = await use_case.execute(
            report_id,
            payload.status,
            datetime.fromisoformat(payload.processing_started_at) if payload.processing_started_at else None,
            datetime.fromisoformat(payload.completed_at) if payload.completed_at else None,
            payload.error_message
        )

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав на обновление этого отчёта")

        return {
            "detail": "Статус обновлён",
            "status": updated.status,
            "completed_at": updated.completed_at.isoformat() if updated.completed_at else None
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления статуса отчёта {report_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{report_id}/file-url")
async def add_report_file_url(
    report_id: UUID,
    payload: ReportFileUrlAdd,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Добавление файла к отчёту {report_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = AddReportFileUrlUseCase(ReportRepositoryImpl(db))
        updated = await use_case.execute(report_id, payload.file_url)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {"detail": "Ссылка добавлена", "file_urls": updated.file_urls}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка добавления файла к отчёту {report_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{report_id}/file-urls")
async def set_report_file_urls(
    report_id: UUID,
    payload: ReportFileUrlsSet,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Установка списка файлов отчёта {report_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = SetReportFileUrlsUseCase(ReportRepositoryImpl(db))
        updated = await use_case.execute(report_id, payload.file_urls)

        if str(updated.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        return {"detail": "Список файлов обновлён", "file_urls": updated.file_urls}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка установки файлов отчёта {report_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{report_id}")
async def delete_report(
    report_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление отчёта {report_id} пользователем {current_user_id}", service="survey-service")

    try:
        use_case = DeleteReportUseCase(ReportRepositoryImpl(db))
        await use_case.execute(report_id)

        return {"detail": "Отчёт удалён"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления отчёта {report_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")