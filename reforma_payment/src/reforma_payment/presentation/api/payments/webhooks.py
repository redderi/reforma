from fastapi import APIRouter, Request, Header, Depends, HTTPException
from reforma_payment.infrastructure.repositories.payment_repository_impl import PaymentRepositoryImpl
from reforma_payment.infrastructure.repositories.payment_provider_repository_impl import PaymentProviderRepositoryImpl
from reforma_payment.application.payments.payments_webhook_use_case import PaymentWebhookUseCase
from reforma_payment.presentation.dependencies.get_db import get_db
from reforma_payment.infrastructure.rabbitmq.publisher import EventPublisher
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_common.logger import log_error

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

event_publisher = EventPublisher()


@router.post("/{provider_type}")
async def payment_webhook(
    provider_type: str,
    request: Request,
    signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    payload = await request.body()
    payment_repo = PaymentRepositoryImpl(db)
    provider_repo = PaymentProviderRepositoryImpl(db)

    use_case = PaymentWebhookUseCase(payment_repo, provider_repo, event_publisher)

    try:
        result = await use_case.execute(payload, signature, provider_type)
        return result
    except ValueError as e:
        log_error(f"Error in {provider_type} webhook: {e}", service="payment-service")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected error in {provider_type} webhook: {e}", service="payment-service")
        raise HTTPException(status_code=500, detail="Internal server error")
