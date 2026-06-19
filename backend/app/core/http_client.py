import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator
from typing import Optional

import httpx

from .config import get_settings
from .pool_observability import (
    configure_http_pool,
    http_request_completed,
    http_request_failed,
    http_request_started,
    mark_http_client_closed,
    mark_http_client_initialized,
)

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
    configure_http_pool(
        max_connections=settings.HTTP_POOL_MAX_CONNECTIONS,
        max_keepalive_connections=settings.HTTP_POOL_MAX_KEEPALIVE_CONNECTIONS,
        pool_timeout_sec=settings.HTTP_POOL_TIMEOUT_SEC,
    )
    mark_http_client_initialized()
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
        mark_http_client_closed()
        logger.info("[HTTP POOL] Closed shared AsyncClient.")


@asynccontextmanager
async def stream_with_pool_metrics(method: str, url: str, **kwargs: object) -> AsyncIterator[httpx.Response]:
    """
    Shared HTTP stream helper that records pooled-request latency and timeout/error counters.
    """
    started_at = http_request_started()
    client = get_http_client()
    try:
        async with client.stream(method, url, **kwargs) as response:
            yield response
            http_request_completed(started_at, response.status_code)
    except Exception as exc:
        http_request_failed(started_at, exc)
        raise
