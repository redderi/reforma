from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from reforma_survey.presentation.schemas.branching_rule_schema import (
    BranchingRuleAnswerUpdate,
    BranchingRuleCreate,
    BranchingRuleNextQuestionUpdate,
    BranchingRuleOut,
)
from reforma_survey.domain.entities.branching_rule import BranchingRule
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
from reforma_survey.infrastructure.repositories.branching_rule_repository_impl import (
    BranchingRuleRepositoryImpl,
)

from reforma_survey.application.branching_rule.get_branching_rule_by_id_use_case import (
    GetBranchingRuleByIdUseCase,
)
from reforma_survey.application.branching_rule.get_branching_rules_by_question_use_case import (
    GetBranchingRulesByQuestionUseCase,
)
from reforma_survey.application.branching_rule.create_branching_rule_use_case import (
    CreateBranchingRuleUseCase,
)
from reforma_survey.application.branching_rule.update_branching_rule_answer_value_use_case import (
    UpdateBranchingRuleAnswerValueUseCase,
)
from reforma_survey.application.branching_rule.update_branching_rule_next_question_use_case import (
    UpdateBranchingRuleNextQuestionUseCase,
)
from reforma_survey.application.branching_rule.set_branching_rule_as_default_use_case import (
    SetBranchingRuleAsDefaultUseCase,
)
from reforma_survey.application.branching_rule.delete_branching_rule_use_case import (
    DeleteBranchingRuleUseCase,
)

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Branching Rules"])


@router.get(
    "/{survey_id}/questions/{question_id}/branching-rules",
    response_model=List[BranchingRuleOut],
)
async def get_branching_rules_for_question(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve branching rules for question",
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
            raise HTTPException(status_code=403, detail="No access to survey")

        question_repo = QuestionRepositoryImpl(db)
        question_exists = await question_repo.exists(question_id)
        if not question_exists:
            log_warning(
                "Question not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"question_id": str(question_id)},
            )
            raise HTTPException(status_code=404, detail="Question not found")

        use_case = GetBranchingRulesByQuestionUseCase(BranchingRuleRepositoryImpl(db))
        rules = await use_case.execute(question_id)

        log_info(
            "Branching rules retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(survey_id),
                "question_id": str(question_id),
                "rules_count": len(rules),
            },
        )

        return [
            BranchingRuleOut(
                id=str(r.id),
                question_id=str(r.question_id),
                answer_value=r.answer_value,
                next_question_id=str(r.next_question_id),
                is_default=r.is_default,
            )
            for r in rules
        ]

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving branching rules",
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


@router.get(
    "/{survey_id}/questions/{question_id}/branching-rules/{rule_id}",
    response_model=BranchingRuleOut,
)
async def get_branching_rule(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Retrieve specific branching rule",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "rule_id": str(rule_id),
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
                "User does not have access to survey",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No access")

        use_case = GetBranchingRuleByIdUseCase(BranchingRuleRepositoryImpl(db))
        rule = await use_case.execute(rule_id)

        if not rule:
            log_warning(
                "Branching rule not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"rule_id": str(rule_id)},
            )
            raise HTTPException(status_code=404, detail="Branching rule not found")

        if rule.question_id != question_id:
            log_warning(
                "Branching rule does not belong to this question",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "rule_id": str(rule_id),
                    "expected_question_id": str(question_id),
                    "actual_question_id": str(rule.question_id),
                },
            )
            raise HTTPException(
                status_code=404,
                detail="Branching rule does not belong to this question",
            )

        log_info(
            "Branching rule retrieved successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id)},
        )

        return BranchingRuleOut(
            id=str(rule.id),
            question_id=str(rule.question_id),
            answer_value=rule.answer_value,
            next_question_id=str(rule.next_question_id),
            is_default=rule.is_default,
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error(
            "Unexpected error retrieving branching rule",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "survey_id": str(survey_id),
                "question_id": str(question_id),
                "rule_id": str(rule_id),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{survey_id}/questions/{question_id}/branching-rules",
    response_model=BranchingRuleOut,
    status_code=201,
)
async def create_branching_rule(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    payload: BranchingRuleCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Create branching rule attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "answer_value": payload.answer_value,
            "next_question_id": str(payload.next_question_id),
            "is_default": payload.is_default,
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
                "User does not have permission to create branching rule",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        question_repo = QuestionRepositoryImpl(db)
        question_exists = await question_repo.exists(question_id)
        if not question_exists:
            log_warning(
                "Question not found",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"question_id": str(question_id)},
            )
            raise HTTPException(status_code=404, detail="Question not found")

        rule = BranchingRule(
            id=uuid4(),
            question_id=question_id,
            answer_value=payload.answer_value.strip(),
            next_question_id=payload.next_question_id,
            is_default=payload.is_default,
        )

        use_case = CreateBranchingRuleUseCase(BranchingRuleRepositoryImpl(db))
        created = await use_case.execute(rule)

        log_info(
            "Branching rule created successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(created.id)},
        )

        return BranchingRuleOut(
            id=str(created.id),
            question_id=str(created.question_id),
            answer_value=created.answer_value,
            next_question_id=str(created.next_question_id),
            is_default=created.is_default,
        )

    except ValueError as e:
        log_warning(
            "Branching rule creation failed",
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
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error during branching rule creation",
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


@router.patch(
    "/{survey_id}/questions/{question_id}/branching-rules/{rule_id}/answer-value",
    response_model=BranchingRuleOut,
)
async def update_branching_rule_answer_value(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    payload: BranchingRuleAnswerUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update branching rule answer value attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "rule_id": str(rule_id),
            "new_answer_value": payload.answer_value,
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
                "User does not have permission to update branching rule",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = UpdateBranchingRuleAnswerValueUseCase(
            BranchingRuleRepositoryImpl(db)
        )
        updated = await use_case.execute(rule_id, payload.answer_value)

        log_info(
            "Branching rule answer value updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id)},
        )

        return BranchingRuleOut(
            id=str(updated.id),
            question_id=str(updated.question_id),
            answer_value=updated.answer_value,
            next_question_id=str(updated.next_question_id),
            is_default=updated.is_default,
        )

    except ValueError as e:
        log_warning(
            "Branching rule answer value update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating branching rule answer value",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/{survey_id}/questions/{question_id}/branching-rules/{rule_id}/next-question",
    response_model=BranchingRuleOut,
)
async def update_branching_rule_next_question(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    payload: BranchingRuleNextQuestionUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Update branching rule next question attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "rule_id": str(rule_id),
            "new_next_question_id": str(payload.next_question_id),
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
                "User does not have permission to update branching rule",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = UpdateBranchingRuleNextQuestionUseCase(
            BranchingRuleRepositoryImpl(db)
        )
        updated = await use_case.execute(rule_id, payload.next_question_id)

        log_info(
            "Branching rule next question updated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id)},
        )

        return BranchingRuleOut(
            id=str(updated.id),
            question_id=str(updated.question_id),
            answer_value=updated.answer_value,
            next_question_id=str(updated.next_question_id),
            is_default=updated.is_default,
        )

    except ValueError as e:
        log_warning(
            "Branching rule next question update failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error updating branching rule next question",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")



@router.delete("/{survey_id}/questions/{question_id}/branching-rules/{rule_id}")
async def delete_branching_rule(
    request: Request,
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)

    log_info(
        "Delete branching rule attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "survey_id": str(survey_id),
            "question_id": str(question_id),
            "rule_id": str(rule_id),
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
                "User does not have permission to delete branching rule",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={"survey_id": str(survey_id)},
            )
            raise HTTPException(status_code=403, detail="No permission")

        use_case = DeleteBranchingRuleUseCase(BranchingRuleRepositoryImpl(db))
        await use_case.execute(rule_id)

        log_info(
            "Branching rule deleted successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id)},
        )

        return {"detail": "Branching rule deleted"}

    except ValueError as e:
        log_warning(
            "Branching rule deletion failed",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        log_error(
            "Unexpected error deleting branching rule",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"rule_id": str(rule_id), "error_detail": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")
