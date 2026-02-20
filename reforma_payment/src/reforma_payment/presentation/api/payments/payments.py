from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_payment.infrastructure.repositories.payment_repository_impl import (
    PaymentRepositoryImpl,
)
from reforma_payment.infrastructure.repositories.payment_provider_repository_impl import (
    PaymentProviderRepositoryImpl,
)
from reforma_payment.application.payments.create_payment_use_case import (
    CreatePaymentUseCase,
)
from reforma_payment.presentation.schemas.create_payment_request_schema import (
    CreatePaymentRequest,
)
from reforma_payment.presentation.dependencies.get_db import get_db
from reforma_common.logger import log_info, log_warning, log_error

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate")
async def create_payment(
    request: Request,
    payment_request: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db),
):
    trace_id = getattr(request.state, "trace_id", None)
    log_info(
        "Payment initiation attempt",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "provider_type": payment_request.provider_type,
        },
    )
    try:
        payment_repo = PaymentRepositoryImpl(db)
        provider_repo = PaymentProviderRepositoryImpl(db)
        use_case = CreatePaymentUseCase(payment_repo, provider_repo)
        payment = await use_case.execute(payment_request)
        log_info(
            "Payment initiated successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={
                "payment_id": str(payment.id),
                "amount": payment.amount,
                "currency": payment.currency,
                "provider_type": payment.provider_type,
            },
        )

        return payment.__dict__
    except ValueError as e:
        log_warning(
            "Payment initiation failed due to validation/business error",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={
                "amount": payment_request.amount,
                "currency": payment_request.currency,
                "provider_type": payment_request.provider_type,
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(
            "Unexpected error during payment initiation",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={
                "amount": payment_request.amount,
                "currency": payment_request.currency,
                "provider_type": payment_request.provider_type,
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")
