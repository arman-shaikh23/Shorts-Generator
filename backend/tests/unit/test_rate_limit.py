import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.rate_limit import _SlidingWindowLimiter  # noqa: E402


@pytest.mark.asyncio
async def test_sliding_window_limiter_allows_then_blocks():
    limiter = _SlidingWindowLimiter(max_keys=100)

    allowed_1, remaining_1, retry_after_1 = await limiter.allow("client:/path", limit=2, window_sec=60)
    allowed_2, remaining_2, retry_after_2 = await limiter.allow("client:/path", limit=2, window_sec=60)
    blocked, remaining_3, retry_after_3 = await limiter.allow("client:/path", limit=2, window_sec=60)

    assert allowed_1 is True
    assert allowed_2 is True
    assert blocked is False
    assert remaining_1 == 1
    assert remaining_2 == 0
    assert remaining_3 == 0
    assert retry_after_1 == 0
    assert retry_after_2 == 0
    assert retry_after_3 >= 1

