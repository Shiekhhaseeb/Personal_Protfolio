from __future__ import annotations

import time
from collections import defaultdict, deque

from app.config import get_settings


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        hits = self._hits[client_id]

        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= self.max_requests:
            return False

        hits.append(now)
        return True


_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        settings = get_settings()
        _limiter = RateLimiter(max_requests=settings.chat_rate_limit)
    return _limiter
