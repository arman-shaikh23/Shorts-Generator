import logging
from typing import Optional

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)

_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        settings = get_settings()
        limits = httpx.Limits(
            max_connections=settings.HTTP_POOL_MAX_CONNECTIONS,
            max_keepalive_connections=settings.HTTP_POOL_MAX_KEEPALIVE_CONNECTIONS,
        )
        timeout = httpx.Timeout(
            connect=settings.HTTP_CONNECT_TIMEOUT_SEC,
            read=settings.HTTP_READ_TIMEOUT_SEC,
            write=settings.HTTP_WRITE_TIMEOUT_SEC,
            pool=settings.HTTP_POOL_TIMEOUT_SEC,
        )
        _http_client = httpx.AsyncClient(
            follow_redirects=True,
            limits=limits,
            timeout=timeout,
        )
    return _http_client


async def connect_http_client() -> None:
    get_http_client()
    settings = get_settings()
    logger.info(
        "[HTTP POOL] Initialized shared AsyncClient: max_connections=%s keepalive=%s",
        settings.HTTP_POOL_MAX_CONNECTIONS,
        settings.HTTP_POOL_MAX_KEEPALIVE_CONNECTIONS,
    )


async def close_http_client() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("[HTTP POOL] Closed shared AsyncClient.")
