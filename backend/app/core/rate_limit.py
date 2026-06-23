import asyncio
import time
from collections import deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings


class _SlidingWindowLimiter:
    def __init__(self, max_keys: int) -> None:
        self._events: dict[str, deque[float]] = {}
        self._max_keys = max(100, int(max_keys))
        self._lock = asyncio.Lock()
        self._last_cleanup = time.monotonic()

    async def allow(self, key: str, limit: int, window_sec: int) -> tuple[bool, int, int]:
        now = time.monotonic()
        cutoff = now - max(1, window_sec)
        safe_limit = max(1, int(limit))

        async with self._lock:
            bucket = self._events.setdefault(key, deque())

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= safe_limit:
                retry_after = max(1, int(window_sec - (now - bucket[0])))
                return False, 0, retry_after

            bucket.append(now)
            remaining = max(0, safe_limit - len(bucket))

            if now - self._last_cleanup > 30:
                self._cleanup_stale_entries_locked(cutoff)
                self._last_cleanup = now

            return True, remaining, 0

    def _cleanup_stale_entries_locked(self, cutoff: float) -> None:
        stale_keys: list[str] = []
        for key, bucket in self._events.items():
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if not bucket:
                stale_keys.append(key)
        for key in stale_keys:
            self._events.pop(key, None)

        if len(self._events) > self._max_keys:
            # Trim oldest keys in a bounded way to avoid unbounded memory growth.
            for key in list(self._events.keys())[: len(self._events) - self._max_keys]:
                self._events.pop(key, None)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.enabled = bool(settings.ENABLE_RATE_LIMITING)
        self.default_limit = max(1, settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
        self.auth_limit = max(1, settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE)
        self.generation_limit = max(1, settings.RATE_LIMIT_GENERATION_REQUESTS_PER_MINUTE)
        self.window_sec = 60
        self.trust_proxy = bool(settings.RATE_LIMIT_TRUST_PROXY)
        self.excluded_prefixes = tuple(
            p.strip() for p in settings.RATE_LIMIT_EXCLUDE_PATHS.split(",") if p.strip()
        )
        self.limiter = _SlidingWindowLimiter(max_keys=settings.RATE_LIMIT_MAX_KEYS)

    async def dispatch(self, request: Request, call_next):
        if not self.enabled or request.method.upper() == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if self._is_excluded(path):
            return await call_next(request)

        limit = self._resolve_limit_for_path(path)
        client_id = self._get_client_id(request)
        key = f"{client_id}:{path}"

        allowed, remaining, retry_after = await self.limiter.allow(key, limit, self.window_sec)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please retry later.",
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _is_excluded(self, path: str) -> bool:
        for prefix in self.excluded_prefixes:
            if path.startswith(prefix):
                return True
        return False

    def _resolve_limit_for_path(self, path: str) -> int:
        if path.startswith("/api/v1/auth"):
            return self.auth_limit
        if "/generation/" in path:
            return self.generation_limit
        return self.default_limit

    def _get_client_id(self, request: Request) -> str:
        if self.trust_proxy:
            forwarded_for = request.headers.get("X-Forwarded-For", "")
            first = forwarded_for.split(",")[0].strip()
            if first:
                return first[:120]

        if request.client and request.client.host:
            return request.client.host[:120]
        return "unknown"

