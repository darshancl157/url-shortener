import unittest

from app.core.exceptions import TooManyRequestsError
from app.core.rate_limit import RateLimiter


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class RateLimiterTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.limiter = RateLimiter(clock=self.clock)

    def test_allows_up_to_the_limit_then_blocks_with_retry_after(self):
        for _ in range(3):
            self.limiter.check("k", limit=3, window_seconds=60)
        with self.assertRaises(TooManyRequestsError) as ctx:
            self.limiter.check("k", limit=3, window_seconds=60)
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(ctx.exception.headers, {"Retry-After": "60"})

    def test_window_slides(self):
        self.limiter.check("k", 2, 60)
        self.clock.t += 30
        self.limiter.check("k", 2, 60)
        self.clock.t += 31  # the first hit is now older than 60 s
        self.limiter.check("k", 2, 60)  # allowed again
        with self.assertRaises(TooManyRequestsError) as ctx:
            self.limiter.check("k", 2, 60)
        self.assertEqual(ctx.exception.headers["Retry-After"], "29")

    def test_keys_are_independent(self):
        self.limiter.check("a", 1, 60)
        self.limiter.check("b", 1, 60)  # a different key has its own budget
        with self.assertRaises(TooManyRequestsError):
            self.limiter.check("a", 1, 60)

    def test_blocked_attempts_are_not_counted(self):
        self.limiter.check("k", 1, 60)
        for _ in range(5):
            with self.assertRaises(TooManyRequestsError):
                self.limiter.check("k", 1, 60)
        self.clock.t += 61
        self.limiter.check("k", 1, 60)  # free again after one window, not five

    def test_sweep_forgets_idle_keys(self):
        limiter = RateLimiter(clock=self.clock, sweep_every=2)
        limiter.check("old", 5, 60)
        self.clock.t += 120
        limiter.check("new", 5, 60)  # second call triggers a sweep
        self.assertNotIn("old", limiter._hits)
        self.assertIn("new", limiter._hits)


if __name__ == "__main__":
    unittest.main()