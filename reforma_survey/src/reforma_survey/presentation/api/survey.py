from fastapi import APIRouter
from reforma_common.logger import log_info

router = APIRouter(prefix="/survey", tags=["survey"])

@router.get("/health")
async def health():
    log_info("health", service="survey-service")
    return {"status": "ok"}
