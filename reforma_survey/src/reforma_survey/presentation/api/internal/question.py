from fastapi import APIRouter, Request, HTTPException, Depends
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_survey.presentation.dependencies.verify_api_key import verify_api_key
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.domain.repositories.question_repository import QuestionRepository
from reforma_survey.infrastructure.repositories.question_repository_impl import QuestionRepositoryImpl
from reforma_survey.application.question.get_questions_by_survey_use_case import GetQuestionsBySurveyUseCase
from reforma_common.logger import log_info, log_error
from reforma_survey.presentation.schemas.question_schema import QuestionOut

router = APIRouter(prefix="/internal/surveys", tags=["Internal Surveys"])

@router.get("/{survey_id}/questions", response_model=list[QuestionOut])
async def get_questions_by_survey(
    request: Request,
    survey_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_api_key),  
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve questions for survey",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        context={"survey_id": str(survey_id)},
    )

    try:
        repository: QuestionRepository = QuestionRepositoryImpl(db)
        use_case = GetQuestionsBySurveyUseCase(repository)
        questions = await use_case.execute(survey_id)

        if not questions:
            log_info(
                "No questions found for survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                context={"survey_id": str(survey_id)},
            )
            return []

        log_info(
            "Questions retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            context={"survey_id": str(survey_id)},
        )

        # Преобразуем в схему QuestionOut
        return [q.to_dict() for q in questions]

    except Exception as e:
        log_error(
            "Unexpected error retrieving survey questions",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            context={"survey_id": str(survey_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")