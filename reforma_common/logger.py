import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Optional

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
        except Exception as e:
            print(f"[logger] Logstash unreachable: {e}")

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

def log(level: str, message: str, service: str = "unknown", context: Optional[dict] = None, trace_id: Optional[str] = None):
    data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "service": service,
        "message": message,
        "trace_id": trace_id or "",
        "context": context or {}
    }
    log_message = json.dumps(data)

    if level.upper() == "INFO":
        logger.info(log_message)
    elif level.upper() == "ERROR":
        logger.error(log_message)
    elif level.upper() == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)


def log_info(message: str, service="unknown", context: Optional[dict] = None, trace_id: Optional[str] = None):
    log("INFO", message, service, context, trace_id)

def log_error(message: str, service="unknown", context: Optional[dict] = None, trace_id: Optional[str] = None):
    log("ERROR", message, service, context, trace_id)

def log_warning(message: str, service="unknown", context: Optional[dict] = None, trace_id: Optional[str] = None):
    log("WARNING", message, service, context, trace_id)
