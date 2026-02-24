from fastapi import APIRouter, Request, Header, Depends, HTTPException
from reforma_payment.infrastructure.repositories.payment_repository_impl import (
    PaymentRepositoryImpl,
)
from reforma_payment.infrastructure.repositories.payment_provider_repository_impl import (
    PaymentProviderRepositoryImpl,
)
from reforma_payment.application.payments.payments_webhook_use_case import (
    PaymentWebhookUseCase,
)
from reforma_payment.presentation.dependencies.get_db import get_db
from reforma_payment.infrastructure.rabbitmq.publisher import EventPublisher
from sqlalchemy.ext.asyncio import AsyncSession
from reforma_common.logger import log_info, log_warning, log_error
from reforma_payment.presentation.dependencies.get_event_publisher import (
    get_event_publisher,
)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/{provider_type}")
async def payment_webhook(
    request: Request,
    provider_type: str,
    signature: str = Header(None, alias="Stripe-Signature"),  # ← правильный заголовок для Stripe
    db: AsyncSession = Depends(get_db),
    event_publisher: EventPublisher = Depends(get_event_publisher),
):
    payload = await request.body()

    if provider_type == "stripe":
        if not signature:
            raise HTTPException(400, "Missing Stripe-Signature header")
    trace_id = getattr(request.state, "trace_id", None)
    log_info(
        "Received payment webhook",
        service="payment-service",
        request=request,
        trace_id=trace_id,
        context={
            "provider_type": provider_type,
            "signature_present": bool(signature),
            "payload_size_bytes": len(await request.body()),
        },
    )
    try:
        payload = await request.body()
        payment_repo = PaymentRepositoryImpl(db)
        provider_repo = PaymentProviderRepositoryImpl(db)
        use_case = PaymentWebhookUseCase(payment_repo, provider_repo, event_publisher)
        result = await use_case.execute(payload, signature, provider_type)
        log_info(
            "Payment webhook processed successfully",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={
                "provider_type": provider_type,
                "result_status": result.get("status", "unknown")
                if isinstance(result, dict)
                else "processed",
            },
        )
        return result
    except ValueError as e:
        log_warning(
            "Payment webhook validation/business error",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={
                "provider_type": provider_type,
                "signature_present": bool(signature),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_error(
            "Unexpected error processing payment webhook",
            service="payment-service",
            request=request,
            trace_id=trace_id,
            context={
                "provider_type": provider_type,
                "signature_present": bool(signature),
                "error_detail": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="Internal server error")
