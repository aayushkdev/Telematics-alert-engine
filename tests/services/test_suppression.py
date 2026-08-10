from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.exceptions import RedisError

from app.services import suppression


@pytest.mark.asyncio
async def test_disabled_suppression_does_not_use_redis(monkeypatch):
    get_client = MagicMock()
    monkeypatch.setattr(suppression.redis, "get_client", get_client)

    assert await suppression.is_suppressed(1, 2, 0) is False
    await suppression.start_cooldown(1, 2, 0)

    get_client.assert_not_called()


@pytest.mark.asyncio
async def test_suppression_checks_rule_and_vehicle_key(monkeypatch):
    client = MagicMock()
    client.exists = AsyncMock(return_value=1)
    monkeypatch.setattr(suppression.redis, "get_client", lambda: client)

    assert await suppression.is_suppressed(7, 12, 60) is True
    client.exists.assert_awaited_once_with("suppress:7:12")


@pytest.mark.asyncio
async def test_suppression_sets_ttl_after_processing(monkeypatch):
    client = MagicMock()
    client.set = AsyncMock()
    monkeypatch.setattr(suppression.redis, "get_client", lambda: client)

    await suppression.start_cooldown(7, 12, 60)

    client.set.assert_awaited_once_with("suppress:7:12", "1", ex=60)


@pytest.mark.asyncio
async def test_redis_failure_fails_open(monkeypatch):
    client = MagicMock()
    client.exists = AsyncMock(side_effect=RedisError("unavailable"))
    monkeypatch.setattr(suppression.redis, "get_client", lambda: client)

    assert await suppression.is_suppressed(7, 12, 60) is False
