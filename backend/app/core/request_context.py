import time
import uuid
import contextvars

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from structlog import contextvars as structlog_contextvars  # type: ignore
except Exception:
    structlog_contextvars = None

request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
request_start_ctx_var: contextvars.ContextVar[float] = contextvars.ContextVar("request_start", default=0.0)


def get_request_id() -> str:
    request_id = request_id_ctx_var.get()
    return request_id if request_id else "-"


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming_request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        request_id = (incoming_request_id or uuid.uuid4().hex).strip()[:128]

        request_id_token = request_id_ctx_var.set(request_id)
        started_token = request_start_ctx_var.set(time.perf_counter())
        if structlog_contextvars is not None:
            structlog_contextvars.clear_contextvars()
            structlog_contextvars.bind_contextvars(
                request_id=request_id,
                http_method=request.method,
                http_path=request.url.path,
            )

        try:
            response = await call_next(request)
        finally:
            if structlog_contextvars is not None:
                structlog_contextvars.clear_contextvars()
            request_id_ctx_var.reset(request_id_token)
            request_start_ctx_var.reset(started_token)

        response.headers["X-Request-ID"] = request_id
        return response
