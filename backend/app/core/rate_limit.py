"""In-memory sliding-window rate limiter.

Counters live in this process only: they reset on restart and are not shared between
instances. That is fine for a single instance; a shared store (for example Redis) would
provide the same check() so callers don't change.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable

from app.core.exceptions import TooManyRequestsError


class RateLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic, sweep_every: int = 1000):
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()  # sync routes run in a thread pool
        self._calls = 0
        self._sweep_every = sweep_every
        self._longest_window = 0.0

    def check(self, key: str, limit: int, window_seconds: float) -> None:
        """Record one hit for `key`, or raise TooManyRequestsError if the limit is reached."""
        now = self._clock()
        with self._lock:
            self._longest_window = max(self._longest_window, window_seconds)
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()  # drop hits that have slid out of the window
            if len(hits) >= limit:
                retry_after = math.ceil(hits[0] + window_seconds - now)
                raise TooManyRequestsError(retry_after=max(retry_after, 1))
            hits.append(now)
            self._calls += 1
            if self._calls % self._sweep_every == 0:
                self._sweep(now)

    def _sweep(self, now: float) -> None:
        """Forget keys with no recent hits, so memory doesn't grow forever."""
        cutoff = now - self._longest_window
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff]
        for key in stale:
            del self._hits[key]