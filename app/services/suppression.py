import logging

from redis.exceptions import RedisError

from app.core import redis

logger = logging.getLogger(__name__)


def _key(rule_id: int, vehicle_id: int) -> str:
    return f"suppress:{rule_id}:{vehicle_id}"


async def try_acquire(
    rule_id: int, vehicle_id: int, suppress_for_seconds: int
) -> bool:
    """Atomically acquire a cooldown. Redis failures fail open."""
    if suppress_for_seconds <= 0:
        return True

    try:
        return bool(
            await redis.get_client().set(
                _key(rule_id, vehicle_id),
                "1",
                ex=suppress_for_seconds,
                nx=True,
            )
        )
    except RedisError:
        logger.warning("Redis unavailable; processing alert without suppression")
        return True


async def release(rule_id: int, vehicle_id: int, suppress_for_seconds: int) -> None:
    """Release a newly acquired cooldown after a database transaction fails."""
    if suppress_for_seconds <= 0:
        return

    try:
        await redis.get_client().delete(_key(rule_id, vehicle_id))
    except RedisError:
        logger.warning("Redis unavailable; alert cooldown could not be released")
