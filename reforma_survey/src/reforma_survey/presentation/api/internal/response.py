from fastapi import APIRouter, Request, HTTPException, Depends
from uuid import UUID
from reforma_survey.presentation.dependencies.verify_api_key import verify_api_key
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.domain.repositories.response_repository import ResponseRepository
from reforma_survey.infrastructure.repositories.response_repository_impl import (
    ResponseRepositoryImpl,
)
from reforma_survey.application.response.get_response_by_id_use_case import (
    GetResponseByIdUseCase,
)
from reforma_common.logger import log_info, log_error
from reforma_survey.presentation.schemas.response_schema import ResponseOut

router = APIRouter(prefix="/internal/responses", tags=["Internal Responses"])


@router.get("/{response_id}", response_model=ResponseOut | None)
async def get_response_by_id(
    request: Request,
    response_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve response by ID",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        context={"response_id": str(response_id)},
    )

    try:
        repository: ResponseRepository = ResponseRepositoryImpl(db)
        use_case = GetResponseByIdUseCase(repository)
        response = await use_case.execute(response_id)

        if not response:
            log_info(
                "No response found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                context={"response_id": str(response_id)},
            )
            return None

        log_info(
            "Response retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            context={"response_id": str(response_id)},
        )

        return response.to_dict()

    except Exception as e:
        log_error(
            "Unexpected error retrieving response",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            context={"response_id": str(response_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
