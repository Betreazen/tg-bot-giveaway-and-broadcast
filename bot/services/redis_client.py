"""Redis client helper for direct key access (verification, etc.)."""

from redis.asyncio import Redis

_redis: Redis | None = None


def init_redis(redis_instance: Redis) -> None:
    """Store global Redis instance for use in handlers."""
    global _redis
    _redis = redis_instance


def get_redis() -> Redis:
    """Get the global Redis instance."""
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis
