from fastapi import APIRouter, Depends, HTTPException
from reforma_survey.presentation.schemas.branching_rule_schema import BranchingRuleAnswerUpdate, BranchingRuleCreate, BranchingRuleDefaultUpdate, BranchingRuleNextQuestionUpdate, BranchingRuleOut
from reforma_survey.domain.entities.branching_rule import BranchingRule
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import get_current_user_id
from reforma_survey.infrastructure.repositories.survey_repository_impl import SurveyRepositoryImpl
from reforma_survey.infrastructure.repositories.question_repository_impl import QuestionRepositoryImpl
from reforma_survey.infrastructure.repositories.branching_rule_repository_impl import BranchingRuleRepositoryImpl

from reforma_survey.application.branching_rule.get_branching_rule_by_id_use_case import GetBranchingRuleByIdUseCase
from reforma_survey.application.branching_rule.get_branching_rules_by_question_use_case import GetBranchingRulesByQuestionUseCase
from reforma_survey.application.branching_rule.get_default_branching_rule_use_case import GetDefaultBranchingRuleUseCase
from reforma_survey.application.branching_rule.create_branching_rule_use_case import CreateBranchingRuleUseCase
from reforma_survey.application.branching_rule.update_branching_rule_answer_value_use_case import UpdateBranchingRuleAnswerValueUseCase
from reforma_survey.application.branching_rule.update_branching_rule_next_question_use_case import UpdateBranchingRuleNextQuestionUseCase
from reforma_survey.application.branching_rule.set_branching_rule_as_default_use_case import SetBranchingRuleAsDefaultUseCase
from reforma_survey.application.branching_rule.delete_branching_rule_use_case import DeleteBranchingRuleUseCase

from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/surveys", tags=["Branching Rules"])


@router.get("/{survey_id}/questions/{question_id}/branching-rules", response_model=List[BranchingRuleOut])
async def get_branching_rules_for_question(
    survey_id: UUID,
    question_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение правил ветвления для вопроса {question_id} в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа к опросу")

        question_repo = QuestionRepositoryImpl(db)
        question_exists = await question_repo.exists(question_id)
        if not question_exists:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        use_case = GetBranchingRulesByQuestionUseCase(BranchingRuleRepositoryImpl(db))
        rules = await use_case.execute(question_id)

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
        log_error(f"Ошибка получения правил ветвления для вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.get("/{survey_id}/questions/{question_id}/branching-rules/{rule_id}", response_model=BranchingRuleOut)
async def get_branching_rule(
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Получение правила ветвления {rule_id} для вопроса {question_id} в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет доступа")

        use_case = GetBranchingRuleByIdUseCase(BranchingRuleRepositoryImpl(db))
        rule = await use_case.execute(rule_id)

        if not rule:
            raise HTTPException(status_code=404, detail="Правило ветвления не найдено")

        if rule.question_id != question_id:
            raise HTTPException(status_code=404, detail="Правило не принадлежит этому вопросу")

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
        log_error(f"Ошибка получения правила ветвления {rule_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{survey_id}/questions/{question_id}/branching-rules", response_model=BranchingRuleOut, status_code=201)
async def create_branching_rule(
    survey_id: UUID,
    question_id: UUID,
    payload: BranchingRuleCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Создание правила ветвления для вопроса {question_id} в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        question_repo = QuestionRepositoryImpl(db)
        question_exists = await question_repo.exists(question_id)
        if not question_exists:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        rule = BranchingRule(
            id=UUID(),
            question_id=question_id,
            answer_value=payload.answer_value.strip(),
            next_question_id=payload.next_question_id,
            is_default=payload.is_default,
        )

        use_case = CreateBranchingRuleUseCase(BranchingRuleRepositoryImpl(db))
        created = await use_case.execute(rule)

        return BranchingRuleOut(
            id=str(created.id),
            question_id=str(created.question_id),
            answer_value=created.answer_value,
            next_question_id=str(created.next_question_id),
            is_default=created.is_default,
        )

    except ValueError as e:
        log_warning(f"Ошибка создания правила ветвления: {e}", service="survey-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Неожиданная ошибка создания правила ветвления для вопроса {question_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/branching-rules/{rule_id}/answer-value", response_model=BranchingRuleOut)
async def update_branching_rule_answer_value(
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    payload: BranchingRuleAnswerUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление значения ответа в правиле {rule_id} (вопрос {question_id}, опрос {survey_id}) пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = UpdateBranchingRuleAnswerValueUseCase(BranchingRuleRepositoryImpl(db))
        updated = await use_case.execute(rule_id, payload.answer_value)

        return BranchingRuleOut(
            id=str(updated.id),
            question_id=str(updated.question_id),
            answer_value=updated.answer_value,
            next_question_id=str(updated.next_question_id),
            is_default=updated.is_default,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления значения ответа правила {rule_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/branching-rules/{rule_id}/next-question", response_model=BranchingRuleOut)
async def update_branching_rule_next_question(
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    payload: BranchingRuleNextQuestionUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Обновление следующего вопроса в правиле {rule_id} → {payload.next_question_id} (опрос {survey_id}) пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = UpdateBranchingRuleNextQuestionUseCase(BranchingRuleRepositoryImpl(db))
        updated = await use_case.execute(rule_id, payload.next_question_id)

        return BranchingRuleOut(
            id=str(updated.id),
            question_id=str(updated.question_id),
            answer_value=updated.answer_value,
            next_question_id=str(updated.next_question_id),
            is_default=updated.is_default,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка обновления следующего вопроса в правиле {rule_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.patch("/{survey_id}/questions/{question_id}/branching-rules/{rule_id}/default", response_model=BranchingRuleOut)
async def set_branching_rule_default(
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    payload: BranchingRuleDefaultUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Установка дефолтного статуса правила {rule_id} в вопросе {question_id} (опрос {survey_id}) пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = SetBranchingRuleAsDefaultUseCase(BranchingRuleRepositoryImpl(db))
        updated = await use_case.execute(rule_id, payload.is_default)

        return BranchingRuleOut(
            id=str(updated.id),
            question_id=str(updated.question_id),
            answer_value=updated.answer_value,
            next_question_id=str(updated.next_question_id),
            is_default=updated.is_default,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка установки дефолтного статуса правила {rule_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.delete("/{survey_id}/questions/{question_id}/branching-rules/{rule_id}")
async def delete_branching_rule(
    survey_id: UUID,
    question_id: UUID,
    rule_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    log_info(f"Удаление правила ветвления {rule_id} из вопроса {question_id} в опросе {survey_id} пользователем {current_user_id}", service="survey-service")

    try:
        survey_repo = SurveyRepositoryImpl(db)
        survey = await survey_repo.get_by_id(survey_id)
        if not survey:
            raise HTTPException(status_code=404, detail="Опрос не найден")
        if str(survey.owner_id) != str(current_user_id):
            raise HTTPException(status_code=403, detail="Нет прав")

        use_case = DeleteBranchingRuleUseCase(BranchingRuleRepositoryImpl(db))
        await use_case.execute(rule_id)

        return {"detail": "Правило ветвления удалено"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Ошибка удаления правила ветвления {rule_id}: {e}", service="survey-service")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")