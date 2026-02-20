import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional
from fastapi import Request


class AsyncLogstashHandler(logging.Handler):
    def __init__(self, host="logstash", port=5000):
        super().__init__()
        self.host = host
        self.port = port

    async def send(self, message: str):
        try:
            reader, writer = await asyncio.open_connection(self.host, self.port)
            writer.write((message + "\n").encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception:
            return False

    def emit(self, record):
        log = self.format(record)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.send(log))
        else:
            asyncio.run(self.send(log))


logger = logging.getLogger("reforma")
logger.setLevel(logging.INFO)
handler = AsyncLogstashHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(handler)


def log(
    level: str,
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
):
    ctx = (context or {}).copy()
    if request:
        ctx.setdefault("client.ip", request.client.host)
        ctx.setdefault(
            "user_agent.original", request.headers.get("user-agent", "unknown")
        )
        ctx.setdefault("url.path", str(request.url.path))
        ctx.setdefault("http.request.method", request.method)
    data = {
        "@timestamp": datetime.utcnow().isoformat() + "Z",
        "log.level": level.upper(),
        "message": message.strip(),
        "service.name": service,
        "ecs.version": "8.11.0",
        "trace.id": trace_id or "",
    }
    if user_id is not None:
        data["user.id"] = str(user_id) if not isinstance(user_id, str) else user_id
    data.update(extra)
    if ctx:
        data["labels"] = ctx
    log_message = json.dumps(data, ensure_ascii=False)
    if level.upper() == "ERROR":
        logger.error(log_message)
    elif level.upper() == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)


def log_info(
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
):
    log("INFO", message, service, context, trace_id, user_id, request, **extra)


def log_warning(
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
):
    log("WARNING", message, service, context, trace_id, user_id, request, **extra)


def log_error(
    message: str,
    service: str = "unknown",
    context: Optional[dict] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[Any] = None,
    request: Optional[Request] = None,
    **extra: Any,
):
    log("ERROR", message, service, context, trace_id, user_id, request, **extra)
