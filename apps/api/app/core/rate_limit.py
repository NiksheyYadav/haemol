from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.core.config import settings

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None


class RateLimiter:
    def __init__(self) -> None:
        self._memory: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._client = None
        if redis is not None:
            try:
                self._client = redis.from_url(settings.redis_url, decode_responses=True)
                self._client.ping()
            except Exception:
                self._client = None

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        if self._client is not None:
            bucket = f"rate:{key}"
            pipeline = self._client.pipeline()
            pipeline.zremrangebyscore(bucket, 0, now - window_seconds)
            pipeline.zcard(bucket)
            pipeline.zadd(bucket, {str(now): now})
            pipeline.expire(bucket, window_seconds)
            _, count, _, _ = pipeline.execute()
            if int(count) >= limit:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
            return

        with self._lock:
            entries = [entry for entry in self._memory[key] if entry > now - window_seconds]
            if len(entries) >= limit:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
            entries.append(now)
            self._memory[key] = entries


limiter = RateLimiter()


def enforce_hourly_limit(request: Request) -> None:
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    limiter.check(client_ip, settings.rate_limit_per_hour, 3600)
