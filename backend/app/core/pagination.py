import math
from typing import Dict, Optional, Tuple


def normalize_limit(limit: Optional[int], default_limit: int, max_limit: int) -> int:
    resolved = default_limit if limit is None else int(limit)
    resolved = max(1, resolved)
    resolved = min(resolved, max(1, max_limit))
    return resolved


def resolve_page_skip(
    *,
    page: Optional[int],
    skip: Optional[int],
    limit: int,
) -> Tuple[int, int]:
    safe_limit = max(1, int(limit))

    if page is not None:
        safe_page = max(1, int(page))
        safe_skip = (safe_page - 1) * safe_limit
        return safe_page, safe_skip

    if skip is not None:
        safe_skip = max(0, int(skip))
        safe_page = (safe_skip // safe_limit) + 1
        return safe_page, safe_skip

    return 1, 0


def build_pagination_meta(*, total: int, page: int, limit: int, skip: int) -> Dict[str, Optional[int]]:
    safe_total = max(0, int(total))
    safe_page = max(1, int(page))
    safe_limit = max(1, int(limit))
    safe_skip = max(0, int(skip))

    pages = math.ceil(safe_total / safe_limit) if safe_total > 0 else 0
    has_prev = safe_page > 1
    has_next = pages > 0 and safe_page < pages
    prev_page = safe_page - 1 if has_prev else None
    next_page = safe_page + 1 if has_next else None
    prev_skip = max(0, safe_skip - safe_limit) if has_prev else None
    next_skip = safe_skip + safe_limit if has_next else None

    return {
        "total": safe_total,
        "page": safe_page,
        "limit": safe_limit,
        "skip": safe_skip,
        "pages": pages,
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_page": prev_page,
        "next_page": next_page,
        "prev_skip": prev_skip,
        "next_skip": next_skip,
    }
