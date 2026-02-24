import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request

logger = logging.getLogger("reforma")
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter("%(message)s"))

logger.handlers.clear()
logger.addHandler(stream_handler)
logger.propagate = False



def log(
    level: str,
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
) -> None:

    ctx = (context or {}).copy()

    if request:
        if request.client:
            ctx.setdefault("client.ip", request.client.host)

        ctx.setdefault(
            "user_agent.original",
            request.headers.get("user-agent", "unknown"),
        )

        ctx.setdefault("url.path", str(request.url.path))
        ctx.setdefault("http.request.method", request.method)

    log_data = {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "message": message.strip(),
        "log.level": level.upper(),
        "service.name": service,
        "ecs.version": "8.11.0",
        "trace.id": trace_id or "",
    }

    if user_id is not None:
        log_data["user.id"] = str(user_id)

    if ctx:
        log_data["labels"] = ctx

    if extra:
        log_data.update(extra)

    json_log = json.dumps(log_data, ensure_ascii=False)

    level = level.upper()

    if level == "ERROR":
        logger.error(json_log)
    elif level == "WARNING":
        logger.warning(json_log)
    elif level == "DEBUG":
        logger.debug(json_log)
    else:
        logger.info(json_log)



def log_info(
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
) -> None:
    log("INFO", message, service, context, trace_id, user_id, request, **extra)


def log_warning(
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
) -> None:
    log("WARNING", message, service, context, trace_id, user_id, request, **extra)


def log_error(
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
) -> None:
    log("ERROR", message, service, context, trace_id, user_id, request, **extra)


def log_debug(
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
) -> None:
    log("DEBUG", message, service, context, trace_id, user_id, request, **extra)