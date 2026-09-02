"""Request-level idempotency, fast path via Redis.

This is a *performance* optimization, not the source of truth: it lets
a duplicate in-flight request fail fast without hitting the database.
The database's ``UNIQUE`` constraint on ``transactions.idempotency_key``
/ ``payment_orders.idempotency_key`` is what actually guarantees a
request can never be double-applied, since two application processes
could both pass the Redis check in a tight enough race. Callers should
always be prepared to catch an ``IntegrityError`` on insert and treat
it as "already processed" rather than relying on Redis alone.
"""

import redis

from app.core.config import settings


class IdempotencyService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def claim(self, key: str) -> bool:
        """Returns True if this is the first time ``key`` has been seen
        within the TTL window (and claims it); False if it's a repeat.
        """
        redis_key = f"idempotency:{key}"
        was_set = self.redis.set(redis_key, "1", nx=True, ex=settings.idempotency_key_ttl_seconds)
        return bool(was_set)

    def release(self, key: str) -> None:
        """Frees the claim, e.g. after a failed attempt that should be
        retryable rather than permanently deduplicated.
        """
        self.redis.delete(f"idempotency:{key}")
