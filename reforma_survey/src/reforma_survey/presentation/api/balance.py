from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import UUID, uuid4
import httpx
from reforma_survey.presentation.dependencies.get_db import get_db
from reforma_survey.presentation.dependencies.get_current_user_id import (
    get_current_user_id,
)
from reforma_survey.presentation.schemas.balance_schema import TopUpRequest
from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/balance", tags=["Balance"])


@router.post("/topup")
async def topup_balance(
    request: Request,
    topup_data: TopUpRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)
    idempotency_key = topup_data.idempotency_key or str(uuid4())

    log_info(
        "Balance top-up attempt",
        service="survey-service",
        request=request,
        trace_id=trace_id,
        user_id=str(current_user_id),
        context={
            "amount": topup_data.amount,
            "currency": "RUB",
            "idempotency_key": idempotency_key,
            "description": "Balance top-up",
        },
    )

    try:
        resp = httpx.post(
            "http://reforma-payment:8000/payments/topup/initiate",
            json={
                "user_id": str(current_user_id),
                "amount": topup_data.amount,
                "currency": "RUB",
                "idempotency_key": idempotency_key,
                "description": "Пополнение баланса",
                "metadata": {"source": "survey-service"},
            },
            headers={"Authorization": "Bearer internal-payment-token"},
            timeout=8.0,
        )

        if resp.status_code != 200:
            error_detail = resp.json().get("detail", "Payment error")
            log_warning(
                "Payment initiation failed",
                service="survey-service",
                request=request,
                trace_id=trace_id,
                user_id=str(current_user_id),
                context={
                    "amount": topup_data.amount,
                    "status_code": resp.status_code,
                    "error_detail": error_detail,
                },
            )
            raise HTTPException(resp.status_code, error_detail)

        data = resp.json()

        log_info(
            "Payment initiated successfully",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={
                "payment_id": data["payment_id"],
                "status": data["status"],
                "amount": topup_data.amount,
            },
        )

        return {
            "payment_id": data["payment_id"],
            "status": data["status"],
            "redirect_url": data.get("redirect_url"),
            "client_secret": data.get("client_secret"),
        }

    except httpx.TimeoutException:
        log_error(
            "Payment service timeout during top-up",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"amount": topup_data.amount},
        )
        raise HTTPException(504, "Payment service is not responding")

    except Exception as e:
        log_error(
            "Unexpected error during balance top-up",
            service="survey-service",
            request=request,
            trace_id=trace_id,
            user_id=str(current_user_id),
            context={"amount": topup_data.amount, "error_detail": str(e)},
        )
        raise HTTPException(500, "Internal server error")
