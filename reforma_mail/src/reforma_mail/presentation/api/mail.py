from fastapi import APIRouter
from reforma_common.logger import log_info, log_error

router = APIRouter(prefix="/mail", tags=["Mail"])

@router.get("/health")
async def health():
    log_info("health", service="mail-service")
    return {"status": "ok"}
