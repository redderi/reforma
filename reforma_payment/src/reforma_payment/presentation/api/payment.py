from fastapi import APIRouter
from reforma_common.logger import log_info
from reforma_payment.infrastructure.rabbitmq.publisher import EventPublisher

router = APIRouter(prefix="/payment", tags=["Payment"])
event_publisher = EventPublisher()

@router.get("/health")
async def health():
    log_info("health", service="payment-service")
    return {"status": "ok"}
