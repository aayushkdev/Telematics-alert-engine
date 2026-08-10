import logging

from redis.exceptions import RedisError

from app.core import redis
from app.models import Rule, Telemetry

logger = logging.getLogger(__name__)


def _key(rule_id: int, vehicle_id: int) -> str:
    return f"window:{rule_id}:{vehicle_id}"


async def threshold_reached(rule: Rule, telemetry: Telemetry) -> bool:
    """Record a matching event and report whether its window has reached a rule's minimum."""
    if rule.window_seconds is None or rule.min_matching_events is None:
        return False

    timestamp = telemetry.timestamp.timestamp()
    cutoff = timestamp - rule.window_seconds
    key = _key(rule.id, telemetry.vehicle_id)

    try:
        pipeline = redis.get_client().pipeline(transaction=True)
        pipeline.zadd(key, {telemetry.event_id: timestamp})
        pipeline.zremrangebyscore(key, "-inf", f"({cutoff}")
        pipeline.zcount(key, cutoff, "+inf")
        pipeline.expire(key, rule.window_seconds + 1)
        results = await pipeline.execute()
    except RedisError:
        logger.warning("Redis unavailable; windowed rule was not evaluated")
        return False

    matching_events = results[2]
    return matching_events >= rule.min_matching_events
