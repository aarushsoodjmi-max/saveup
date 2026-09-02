from collections.abc import Generator

import redis

from app.core.config import settings

redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
    max_connections=50,
)


def get_redis_client() -> redis.Redis:
    """Return a Redis client bound to the shared connection pool.

    Safe to call repeatedly -- connections are pooled, not re-opened.
    """
    return redis.Redis(connection_pool=redis_pool)


def get_redis() -> Generator[redis.Redis, None, None]:
    """FastAPI dependency that yields a pooled Redis client."""
    client = get_redis_client()
    try:
        yield client
    finally:
        # Connections are returned to the pool automatically; nothing to
        # close explicitly per-request.
        pass


def ping() -> bool:
    """Used by the health endpoint to verify Redis connectivity."""
    try:
        return get_redis_client().ping()
    except redis.RedisError:
        return False
