from fastapi import APIRouter
from reforma_common.logger import log_info

router = APIRouter(prefix="/payment", tags=["Payment"])

@router.get("/health")
async def health():
    log_info("health", service="payment-service")
    return {"status": "ok"}
