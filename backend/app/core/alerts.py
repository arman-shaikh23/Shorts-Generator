import time
import logging
from typing import Any

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)

_last_alert_sent_by_key: dict[str, float] = {}


def _can_send_alert(alert_key: str, cooldown_sec: int) -> bool:
    now = time.time()
    last_sent = _last_alert_sent_by_key.get(alert_key, 0.0)
    if now - last_sent < max(1, cooldown_sec):
        return False
    _last_alert_sent_by_key[alert_key] = now
    return True


async def send_alert(
    *,
    event: str,
    message: str,
    severity: str = "warning",
    details: dict[str, Any] | None = None,
    alert_key: str | None = None,
) -> bool:
    settings = get_settings()
    if not settings.ENABLE_ALERTS:
        return False
    if not settings.ALERT_WEBHOOK_URL:
        return False

    key = alert_key or event
    if not _can_send_alert(key, settings.ALERT_COOLDOWN_SEC):
        return False

    payload = {
        "service": settings.SERVICE_NAME,
        "environment": settings.SERVICE_ENV,
        "event": event,
        "severity": severity,
        "message": message,
        "details": details or {},
        "timestamp_unix": int(time.time()),
    }

    try:
        async with httpx.AsyncClient(timeout=settings.ALERT_HTTP_TIMEOUT_SEC) as client:
            response = await client.post(settings.ALERT_WEBHOOK_URL, json=payload)
            if response.status_code >= 400:
                logger.warning(
                    "[ALERT] Webhook returned error status=%s body=%s",
                    response.status_code,
                    response.text[:200],
                )
                return False
            return True
    except Exception as exc:
        logger.warning("[ALERT] Failed to send alert event=%s error=%s", event, exc)
        return False

