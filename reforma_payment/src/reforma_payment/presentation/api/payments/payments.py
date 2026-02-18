from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_payment.infrastructure.repositories.payment_repository_impl import PaymentRepositoryImpl
from reforma_payment.infrastructure.repositories.payment_provider_repository_impl import PaymentProviderRepositoryImpl
from reforma_payment.application.payments.create_payment_use_case import CreatePaymentUseCase
from reforma_payment.presentation.schemas.create_payment_request_schema import CreatePaymentRequest
from reforma_payment.presentation.dependencies.get_db import get_db
from reforma_common.logger import log_error

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/initiate")
async def create_payment(
    request: CreatePaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        payment_repo = PaymentRepositoryImpl(db)
        provider_repo = PaymentProviderRepositoryImpl(db)
        use_case = CreatePaymentUseCase(payment_repo, provider_repo)
        payment = await use_case.execute(request)
        return payment.__dict__
    except ValueError as e:
        log_error(f"Payment creation failed: {e}", service="payment-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")
