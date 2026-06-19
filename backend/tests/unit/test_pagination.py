import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.pagination import build_pagination_meta, normalize_limit, resolve_page_skip


def test_normalize_limit_uses_default_when_none():
    assert normalize_limit(None, default_limit=20, max_limit=100) == 20


def test_normalize_limit_clamps_min_and_max():
    assert normalize_limit(0, default_limit=20, max_limit=100) == 1
    assert normalize_limit(999, default_limit=20, max_limit=100) == 100


def test_resolve_page_skip_prefers_page_when_provided():
    page, skip = resolve_page_skip(page=3, skip=5, limit=10)
    assert page == 3
    assert skip == 20


def test_resolve_page_skip_derives_page_from_skip():
    page, skip = resolve_page_skip(page=None, skip=25, limit=10)
    assert page == 3
    assert skip == 25


def test_build_pagination_meta_contains_navigation_fields():
    meta = build_pagination_meta(total=95, page=2, limit=10, skip=10)
    assert meta["pages"] == 10
    assert meta["has_prev"] is True
    assert meta["has_next"] is True
    assert meta["prev_page"] == 1
    assert meta["next_page"] == 3
    assert meta["prev_skip"] == 0
    assert meta["next_skip"] == 20
