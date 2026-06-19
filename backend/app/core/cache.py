import json
import logging
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder

from .config import get_settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis_async  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    redis_async = None

_cache_client: Optional[Any] = None
_force_cache_ready_for_tests: bool = False


def _to_key_part(value: Any) -> str:
    return str(value)


def _is_cache_ready() -> bool:
    if _force_cache_ready_for_tests and _cache_client is not None:
        return True
    settings = get_settings()
    return bool(settings.ENABLE_REDIS_CACHE and _cache_client is not None)


async def connect_cache() -> None:
    global _cache_client
    settings = get_settings()

    if not settings.ENABLE_REDIS_CACHE:
        logger.info("[CACHE] Redis cache is disabled by configuration.")
        return

    if redis_async is None:
        logger.warning("[CACHE] ENABLE_REDIS_CACHE=true but redis package is not available.")
        return

    if _cache_client is not None:
        return

    try:
        _cache_client = redis_async.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SEC,
            socket_timeout=settings.REDIS_READ_TIMEOUT_SEC,
            health_check_interval=30,
        )
        await _cache_client.ping()
        logger.info(
            "[CACHE] Connected to Redis url=%s max_connections=%s",
            settings.REDIS_URL,
            settings.REDIS_MAX_CONNECTIONS,
        )
    except Exception as exc:
        logger.warning("[CACHE] Redis connect failed, cache disabled fallback: %s", exc)
        _cache_client = None


async def close_cache() -> None:
    global _cache_client
    if _cache_client is not None:
        try:
            await _cache_client.aclose()
            logger.info("[CACHE] Redis client closed.")
        finally:
            _cache_client = None


async def cache_get(cache_key: str) -> Optional[Any]:
    if not _is_cache_ready():
        return None

    try:
        payload = await _cache_client.get(cache_key)
        if payload is None:
            return None
        return json.loads(payload)
    except Exception as exc:
        logger.warning("[CACHE] GET failed key=%s error=%s", cache_key, exc)
        return None


async def cache_set(cache_key: str, value: Any, ttl_sec: Optional[int] = None) -> None:
    if not _is_cache_ready():
        return

    settings = get_settings()
    ttl = int(ttl_sec if ttl_sec is not None else settings.CACHE_DEFAULT_TTL_SEC)
    ttl = max(1, ttl)
    payload = json.dumps(jsonable_encoder(value), separators=(",", ":"), ensure_ascii=True)

    try:
        await _cache_client.set(cache_key, payload, ex=ttl)
    except Exception as exc:
        logger.warning("[CACHE] SET failed key=%s error=%s", cache_key, exc)


def _user_projects_version_key(user_id: Any) -> str:
    return f"rf:ver:u:{_to_key_part(user_id)}:projects"


def _user_history_version_key(user_id: Any) -> str:
    return f"rf:ver:u:{_to_key_part(user_id)}:history"


def _user_stats_version_key(user_id: Any) -> str:
    return f"rf:ver:u:{_to_key_part(user_id)}:stats"


def _project_detail_version_key(project_id: Any) -> str:
    return f"rf:ver:p:{_to_key_part(project_id)}:detail"


def _project_uploads_version_key(project_id: Any) -> str:
    return f"rf:ver:p:{_to_key_part(project_id)}:uploads"


async def _get_namespace_version(version_key: str) -> int:
    if not _is_cache_ready():
        return 1

    try:
        current = await _cache_client.get(version_key)
        if current is None:
            return 1
        return max(1, int(current))
    except Exception:
        return 1


async def _bump_namespace_version(version_key: str) -> int:
    if not _is_cache_ready():
        return 1

    settings = get_settings()
    try:
        ttl = int(settings.CACHE_VERSION_TTL_SEC)
        current_value = await _cache_client.get(version_key)
        if current_value is None:
            new_value = 2
            await _cache_client.set(version_key, str(new_value), ex=ttl)
            return new_value

        new_value = int(await _cache_client.incr(version_key))
        await _cache_client.expire(version_key, ttl)
        return max(1, new_value)
    except Exception as exc:
        logger.warning("[CACHE] Version bump failed key=%s error=%s", version_key, exc)
        return 1


async def build_projects_list_cache_key(user_id: Any, page: int, limit: int, skip: int = 0) -> str:
    version = await _get_namespace_version(_user_projects_version_key(user_id))
    return f"rf:cache:u:{_to_key_part(user_id)}:projects:v{version}:p{page}:l{limit}:s{skip}"


async def build_project_detail_cache_key(user_id: Any, project_id: Any) -> str:
    version = await _get_namespace_version(_project_detail_version_key(project_id))
    return f"rf:cache:u:{_to_key_part(user_id)}:project:{_to_key_part(project_id)}:detail:v{version}"


async def build_dashboard_stats_cache_key(user_id: Any) -> str:
    version = await _get_namespace_version(_user_stats_version_key(user_id))
    return f"rf:cache:u:{_to_key_part(user_id)}:stats:v{version}"


async def build_history_cache_key(user_id: Any, page: int, limit: int, skip: int = 0) -> str:
    version = await _get_namespace_version(_user_history_version_key(user_id))
    return f"rf:cache:u:{_to_key_part(user_id)}:history:v{version}:p{page}:l{limit}:s{skip}"


async def build_uploads_cache_key(project_id: Any, mode: str, page: int, limit: int, skip: int = 0) -> str:
    version = await _get_namespace_version(_project_uploads_version_key(project_id))
    return f"rf:cache:p:{_to_key_part(project_id)}:uploads:v{version}:m:{mode}:p{page}:l{limit}:s{skip}"


async def invalidate_after_project_mutation(user_id: Any, project_id: Any) -> None:
    await _bump_namespace_version(_user_projects_version_key(user_id))
    await _bump_namespace_version(_project_detail_version_key(project_id))
    await _bump_namespace_version(_user_stats_version_key(user_id))


async def invalidate_after_upload_mutation(user_id: Any, project_id: Any) -> None:
    await _bump_namespace_version(_project_uploads_version_key(project_id))
    await _bump_namespace_version(_project_detail_version_key(project_id))
    await _bump_namespace_version(_user_projects_version_key(user_id))
    await _bump_namespace_version(_user_stats_version_key(user_id))


async def invalidate_after_generation_mutation(user_id: Any, project_id: Any) -> None:
    await _bump_namespace_version(_user_history_version_key(user_id))
    await _bump_namespace_version(_user_projects_version_key(user_id))
    await _bump_namespace_version(_project_detail_version_key(project_id))
    await _bump_namespace_version(_user_stats_version_key(user_id))


async def invalidate_after_project_delete(user_id: Any, project_id: Any) -> None:
    await _bump_namespace_version(_user_projects_version_key(user_id))
    await _bump_namespace_version(_user_history_version_key(user_id))
    await _bump_namespace_version(_user_stats_version_key(user_id))
    await _bump_namespace_version(_project_detail_version_key(project_id))
    await _bump_namespace_version(_project_uploads_version_key(project_id))


def set_cache_client_for_tests(client: Any) -> None:
    global _cache_client, _force_cache_ready_for_tests
    _cache_client = client
    _force_cache_ready_for_tests = client is not None
