"""Tests for backend/rate_limiter.py

Run from the project root:
    python tests\rate_test.py
"""
import os
import sys
import threading
import time
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException
from backend.rate_limiter import TokenBucketLimiter, rate_limit


class FakeClock:
    """Replaces time.monotonic so tests don't need real sleeping."""

    def __init__(self, start=1000.0):
        self.now = start
        self._real = time.monotonic

    def __enter__(self):
        time.monotonic = lambda: self.now
        return self

    def __exit__(self, *exc):
        time.monotonic = self._real

    def advance(self, seconds):
        self.now += seconds


def fake_request(host="1.2.3.4"):
    return SimpleNamespace(client=SimpleNamespace(host=host))


def test_allows_up_to_capacity():
    limiter = TokenBucketLimiter(capacity=3, refill_per_second=1)
    with FakeClock():
        for _ in range(3):
            allowed, wait = limiter.allow("a")
            assert allowed is True and wait == 0


def test_blocks_after_capacity():
    limiter = TokenBucketLimiter(capacity=2, refill_per_second=1)
    with FakeClock():
        limiter.allow("a")
        limiter.allow("a")
        result = limiter.allow("a")
        assert result is not None, "allow() returned None when blocked; it must return (False, wait_seconds)"
        allowed, wait = result
        assert allowed is False
        assert wait > 0


def test_refills_over_time():
    limiter = TokenBucketLimiter(capacity=1, refill_per_second=1)
    with FakeClock() as clock:
        assert limiter.allow("a")[0] is True
        assert (limiter.allow("a") or (False, 0))[0] is False
        clock.advance(1.1)
        assert limiter.allow("a")[0] is True


def test_keys_are_independent():
    limiter = TokenBucketLimiter(capacity=1, refill_per_second=0.01)
    with FakeClock():
        assert limiter.allow("user1")[0] is True
        assert limiter.allow("user2")[0] is True


def test_prune_removes_idle_keys():
    limiter = TokenBucketLimiter(capacity=5, refill_per_second=1)
    with FakeClock() as clock:
        limiter.allow("old")
        clock.advance(601)
        limiter._prune(clock.now)
        assert "old" not in limiter._buckets


def test_thread_safety():
    limiter = TokenBucketLimiter(capacity=10, refill_per_second=0.0001)
    results = []

    def worker():
        r = limiter.allow("shared")
        results.append(bool(r and r[0]))

    threads = [threading.Thread(target=worker) for _ in range(100)]
    with FakeClock():
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    assert sum(results) == 10, f"expected exactly 10 allowed, got {sum(results)}"


def test_dependency_raises_429_with_retry_after():
    limiter = TokenBucketLimiter(capacity=1, refill_per_second=0.5)
    dep = rate_limit(limiter)
    with FakeClock():
        dep(fake_request())
        try:
            dep(fake_request())
        except HTTPException as e:
            assert e.status_code == 429
            assert int(e.headers["Retry-After"]) >= 1
        else:
            raise AssertionError("expected HTTPException 429")


def test_dependency_unknown_client():
    limiter = TokenBucketLimiter(capacity=1, refill_per_second=1)
    dep = rate_limit(limiter)
    with FakeClock():
        dep(SimpleNamespace(client=None))


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)

