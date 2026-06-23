import logging
from typing import Any

logger = logging.getLogger(__name__)

_tracing_initialized = False


def _parse_headers(raw_headers: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not raw_headers:
        return result
    parts = [part.strip() for part in raw_headers.split(",") if part.strip()]
    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            result[key] = value
    return result


def setup_tracing(app: Any, settings: Any) -> bool:
    global _tracing_initialized
    if not settings.ENABLE_OTEL:
        return False
    if _tracing_initialized:
        return True

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    except Exception as exc:
        logger.warning("[TRACING] OpenTelemetry packages are unavailable: %s", exc)
        return False

    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME or settings.SERVICE_NAME,
            "service.version": settings.SERVICE_VERSION,
            "deployment.environment": settings.SERVICE_ENV,
        }
    )
    tracer_provider = TracerProvider(resource=resource)

    exporter = None
    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        headers = _parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS)
        exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=headers,
            timeout=settings.OTEL_EXPORTER_TIMEOUT_SEC,
        )
    elif settings.OTEL_ENABLE_CONSOLE_EXPORTER:
        exporter = ConsoleSpanExporter()

    if exporter is None:
        logger.warning(
            "[TRACING] ENABLE_OTEL=true but no exporter configured. "
            "Set OTEL_EXPORTER_OTLP_ENDPOINT or OTEL_ENABLE_CONSOLE_EXPORTER=true."
        )
        return False

    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)

    if settings.OTEL_INSTRUMENT_FASTAPI:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        except Exception as exc:
            logger.warning("[TRACING] Failed to instrument FastAPI: %s", exc)

    if settings.OTEL_INSTRUMENT_HTTPX:
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

            HTTPXClientInstrumentor().instrument()
        except Exception as exc:
            logger.warning("[TRACING] Failed to instrument HTTPX: %s", exc)

    if settings.OTEL_INSTRUMENT_PYMONGO:
        try:
            from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

            PymongoInstrumentor().instrument()
        except Exception as exc:
            logger.warning("[TRACING] Failed to instrument PyMongo: %s", exc)

    if settings.OTEL_INSTRUMENT_LOGGING:
        try:
            from opentelemetry.instrumentation.logging import LoggingInstrumentor

            LoggingInstrumentor().instrument(set_logging_format=False)
        except Exception as exc:
            logger.warning("[TRACING] Failed to instrument logging correlation: %s", exc)

    _tracing_initialized = True
    logger.info("[TRACING] OpenTelemetry tracing initialized.")
    return True
