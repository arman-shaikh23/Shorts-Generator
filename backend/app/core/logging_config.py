import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

from .request_context import get_request_id

try:
    import structlog  # type: ignore
except Exception:
    structlog = None


class FallbackJsonFormatter(logging.Formatter):
    """
    Safety formatter used only when structlog is unavailable.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", get_request_id()),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return _safe_json_dumps(payload)


def _safe_json_dumps(payload: dict[str, Any], **kwargs: Any) -> str:
    import json

    options = {
        "ensure_ascii": True,
        "separators": (",", ":"),
    }
    options.update(kwargs)
    if "default" not in options:
        options["default"] = str
    return json.dumps(payload, **options)


def _add_otel_context(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        span_context = span.get_span_context()
        if span_context and span_context.is_valid:
            event_dict["trace_id"] = f"{span_context.trace_id:032x}"
            event_dict["span_id"] = f"{span_context.span_id:016x}"
    except Exception:
        # Never break request processing because observability context failed.
        pass
    return event_dict


def _add_request_id(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    if "request_id" not in event_dict:
        event_dict["request_id"] = get_request_id()
    return event_dict


def _build_structlog_processor_formatter(log_format: str):
    assert structlog is not None

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        _add_request_id,
        _add_otel_context,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format.lower() == "json":
        renderer = structlog.processors.JSONRenderer(serializer=_safe_json_dumps)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )


def _build_fallback_formatter(log_format: str) -> logging.Formatter:
    if log_format.lower() == "json":
        return FallbackJsonFormatter()
    return logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [req=%(request_id)s] %(message)s")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def _build_better_stack_handler(settings, formatter: logging.Formatter) -> logging.Handler | None:
    if not settings.ENABLE_BETTER_STACK or not settings.BETTER_STACK_SOURCE_TOKEN:
        return None
    try:
        from logtail import LogtailHandler  # type: ignore

        handler = LogtailHandler(source_token=settings.BETTER_STACK_SOURCE_TOKEN)
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        handler.addFilter(RequestIdFilter())
        return handler
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "[LOGGING] Better Stack handler unavailable, continuing without remote log shipping: %s",
            exc,
        )
        return None


def _build_formatter(settings) -> logging.Formatter:
    use_structlog = bool(settings.ENABLE_STRUCTLOG and structlog is not None)
    if use_structlog:
        return _build_structlog_processor_formatter(settings.LOG_FORMAT)
    return _build_fallback_formatter(settings.LOG_FORMAT)


def configure_logging(settings) -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = _build_formatter(settings)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    request_id_filter = RequestIdFilter()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(request_id_filter)
    root_logger.addHandler(stream_handler)

    if settings.LOG_TO_FILE:
        log_file_path = settings.LOG_FILE_PATH
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(request_id_filter)
        root_logger.addHandler(file_handler)

    better_stack_handler = _build_better_stack_handler(settings, formatter)
    if better_stack_handler is not None:
        root_logger.addHandler(better_stack_handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True

    logger = logging.getLogger(__name__)
    logger.info(
        "[LOGGING] Configured level=%s format=%s file=%s structlog=%s better_stack=%s",
        settings.LOG_LEVEL.upper(),
        settings.LOG_FORMAT.lower(),
        bool(settings.LOG_TO_FILE),
        bool(settings.ENABLE_STRUCTLOG and structlog is not None),
        bool(settings.ENABLE_BETTER_STACK and settings.BETTER_STACK_SOURCE_TOKEN),
    )
    if settings.ENABLE_STRUCTLOG and structlog is None:
        logger.warning(
            "[LOGGING] ENABLE_STRUCTLOG=true but structlog package is missing. "
            "Falling back to standard formatter."
        )
