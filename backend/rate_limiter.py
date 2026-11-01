import math
import time
import threading
from fastapi import HTTPException, Request


class TokenBucketLimiter:
    def __init__(self, capacity, refill_per_second):
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._buckets = {}
        self._lock = threading.Lock()
        self._calls = 0

    def allow(self, key):
        now = time.monotonic()
        with self._lock:
            self._calls += 1
            if self._calls % 1000 == 0:
                self._prune(now)

            tokens, last = self._buckets.get(key, (float(self.capacity), now))
            tokens = min(self.capacity, tokens + (now - last) * self.refill_per_second)

            if tokens >= 1:
                self._buckets[key] = (tokens - 1, now)
                return True, 0

            self._buckets[key] = (tokens, now)
            return False, (1 - tokens) / self.refill_per_second

    def _prune(self, now):
        idle_limit = 600
        stale = [k for k, (_, last) in self._buckets.items() if now - last > idle_limit]
        for k in stale:
            del self._buckets[k]


def rate_limit(limiter):
    def dependency(request: Request):
        client = request.client.host if request.client else "unknown"
        allowed, wait = limiter.allow(client)
        if not allowed:
            seconds = max(1, math.ceil(wait))
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Try again in {seconds} seconds.",
                headers={"Retry-After": str(seconds)},
            )
    return dependency