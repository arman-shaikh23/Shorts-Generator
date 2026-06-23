import logging
from typing import Any

logger = logging.getLogger(__name__)

_metrics_initialized = False


def setup_metrics(app: Any, settings: Any) -> bool:
    global _metrics_initialized
    if _metrics_initialized:
        return True
    if not settings.ENABLE_PROMETHEUS_METRICS:
        return False

    try:
        from prometheus_fastapi_instrumentator import Instrumentator
    except Exception as exc:
        logger.warning("[METRICS] prometheus-fastapi-instrumentator unavailable: %s", exc)
        return False

    try:
        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=False,
            should_respect_env_var=False,
            should_instrument_requests_inprogress=True,
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )
        instrumentator.instrument(app).expose(
            app,
            include_in_schema=False,
            endpoint=settings.PROMETHEUS_METRICS_PATH,
        )
        _metrics_initialized = True
        logger.info("[METRICS] Prometheus metrics enabled endpoint=%s", settings.PROMETHEUS_METRICS_PATH)
        return True
    except Exception as exc:
        logger.warning("[METRICS] Failed to initialize Prometheus instrumentation: %s", exc)
        return False

