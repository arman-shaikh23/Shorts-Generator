import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.cache import (  # noqa: E402
    build_history_cache_key,
    build_projects_list_cache_key,
    cache_get,
    cache_set,
    invalidate_after_generation_mutation,
    invalidate_after_project_mutation,
    set_cache_client_for_tests,
)
from app.core.config import get_settings  # noqa: E402


class FakeRedis:
    def __init__(self) -> None:
        self.store = {}
        self.expiry = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value
        if ex is not None:
            self.expiry[key] = ex
        return True

    async def incr(self, key: str):
        current = int(self.store.get(key, "0"))
        current += 1
        self.store[key] = str(current)
        return current

    async def expire(self, key: str, ttl: int):
        self.expiry[key] = ttl
        return True


@pytest.fixture
def redis_cache_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_REDIS_CACHE", "true")
    monkeypatch.setenv("CACHE_DEFAULT_TTL_SEC", "42")
    monkeypatch.setenv("CACHE_VERSION_TTL_SEC", "120")
    get_settings.cache_clear()

    fake = FakeRedis()
    set_cache_client_for_tests(fake)
    yield fake

    set_cache_client_for_tests(None)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_cache_set_get_uses_ttl(redis_cache_enabled):
    await cache_set("rf:test:key", {"ok": True}, ttl_sec=30)
    value = await cache_get("rf:test:key")
    assert value == {"ok": True}
    assert redis_cache_enabled.expiry["rf:test:key"] == 30


@pytest.mark.asyncio
async def test_versioned_keys_change_after_invalidation(redis_cache_enabled):
    key_before = await build_projects_list_cache_key("user-1", page=1, limit=20)
    assert ":v1:" in key_before

    await invalidate_after_project_mutation("user-1", "project-1")
    key_after = await build_projects_list_cache_key("user-1", page=1, limit=20)
    assert ":v2:" in key_after


@pytest.mark.asyncio
async def test_generation_invalidation_bumps_history_namespace(redis_cache_enabled):
    key_before = await build_history_cache_key("user-2", page=1, limit=10)
    assert ":v1:" in key_before

    await invalidate_after_generation_mutation("user-2", "project-9")
    key_after = await build_history_cache_key("user-2", page=1, limit=10)
    assert ":v2:" in key_after
