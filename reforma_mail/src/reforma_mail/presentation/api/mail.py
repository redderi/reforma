from fastapi import APIRouter, Request
from reforma_common.logger import log_info

router = APIRouter(prefix="/mail", tags=["Mail"])


@router.get("/health")
async def health(request: Request):
    trace_id = getattr(request.state, "trace_id", None)
    log_info(
        "Health check request received",
        service="mail-service",
        request=request,
        trace_id=trace_id
    )
    return {"status": "ok"}
