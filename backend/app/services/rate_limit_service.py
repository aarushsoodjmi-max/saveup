"""Fixed-window rate limiting backed by Redis ``INCR`` + ``EXPIRE``.

Not a sliding-window / token-bucket implementation -- deliberately
simple for an MVP. Good enough to blunt OTP-spam and brute-force
attempts; swap for a sliding-window Lua script if precision matters
later.
"""

import redis

from app.core.exceptions import RateLimitedError


class RateLimitService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def hit(self, key: str, *, limit: int, window_seconds: int) -> None:
        """Raises :class:`RateLimitedError` once ``limit`` hits have been
        recorded for ``key`` within the current window.
        """
        redis_key = f"ratelimit:{key}"
        current = self.redis.incr(redis_key)
        if current == 1:
            self.redis.expire(redis_key, window_seconds)

        if current > limit:
            ttl = self.redis.ttl(redis_key)
            retry_after = ttl if ttl and ttl > 0 else window_seconds
            raise RateLimitedError(
                "Too many requests, please try again later",
                details={"retry_after_seconds": retry_after},
            )
