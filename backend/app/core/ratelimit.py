"""Sliding-window rate limiter.

M2 version is in-memory per-process — correct interface, simplest storage.
KNOWN LIMIT (documented tradeoff): multi-worker deploys need shared state; the
storage swaps to Redis in M3 when the redis client lands, same interface.
"""

import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.exceptions import RateLimitError

_hits: dict[str, deque[float]] = defaultdict(deque)


class RateLimiter:
    """Usage: Depends(RateLimiter(times=5, seconds=60)) on a route."""

    def __init__(self, times: int, seconds: int) -> None:
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_ip}"
        now = time.monotonic()
        window = _hits[key]
        while window and now - window[0] > self.seconds:  # evict old hits
            window.popleft()
        if len(window) >= self.times:
            raise RateLimitError("Too many attempts, try again later")
        window.append(now)


def reset() -> None:
    """Test hook — clear all counters."""
    _hits.clear()
