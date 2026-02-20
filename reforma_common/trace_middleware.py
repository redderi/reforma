from uuid import uuid4
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        traceparent = request.headers.get("traceparent")
        if traceparent:
            parts = traceparent.split("-")
            if len(parts) >= 3:
                trace_id = parts[1]
            else:
                trace_id = None
        else:
            trace_id = None
        if not trace_id:
            trace_id = uuid4().hex + uuid4().hex[:4]
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["traceparent"] = f"00-{trace_id}-{'00' * 8}-01"
        return response
