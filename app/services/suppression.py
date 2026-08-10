import logging

from redis.exceptions import RedisError

from app.core import redis

logger = logging.getLogger(__name__)


def _key(rule_id: int, vehicle_id: int) -> str:
    return f"suppress:{rule_id}:{vehicle_id}"


async def is_suppressed(
    rule_id: int, vehicle_id: int, suppress_for_seconds: int
) -> bool:
    """Return false when Redis is unavailable so alerts fail open."""
    if suppress_for_seconds <= 0:
        return False

    try:
        return bool(await redis.get_client().exists(_key(rule_id, vehicle_id)))
    except RedisError:
        logger.warning("Redis unavailable; processing alert without suppression")
        return False


async def start_cooldown(
    rule_id: int, vehicle_id: int, suppress_for_seconds: int
) -> None:
    if suppress_for_seconds <= 0:
        return

    try:
        await redis.get_client().set(
            _key(rule_id, vehicle_id), "1", ex=suppress_for_seconds
        )
    except RedisError:
        logger.warning("Redis unavailable; alert cooldown was not set")
