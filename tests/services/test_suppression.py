from unittest.mock import AsyncMock, MagicMock

import pytest
from redis.exceptions import RedisError

from app.services import suppression


@pytest.mark.asyncio
async def test_disabled_suppression_does_not_use_redis(monkeypatch):
    get_client = MagicMock()
    monkeypatch.setattr(suppression.redis, "get_client", get_client)

    assert await suppression.try_acquire(1, 2, 0) is True
    await suppression.release(1, 2, 0)

    get_client.assert_not_called()


@pytest.mark.asyncio
async def test_suppression_acquires_rule_and_vehicle_key_atomically(monkeypatch):
    client = MagicMock()
    client.set = AsyncMock(return_value=True)
    monkeypatch.setattr(suppression.redis, "get_client", lambda: client)

    assert await suppression.try_acquire(7, 12, 60) is True
    client.set.assert_awaited_once_with("suppress:7:12", "1", ex=60, nx=True)


@pytest.mark.asyncio
async def test_existing_cooldown_is_not_acquired(monkeypatch):
    client = MagicMock()
    client.set = AsyncMock(return_value=None)
    monkeypatch.setattr(suppression.redis, "get_client", lambda: client)

    assert await suppression.try_acquire(7, 12, 60) is False



@pytest.mark.asyncio
async def test_redis_failure_fails_open(monkeypatch):
    client = MagicMock()
    client.set = AsyncMock(side_effect=RedisError("unavailable"))
    monkeypatch.setattr(suppression.redis, "get_client", lambda: client)

    assert await suppression.try_acquire(7, 12, 60) is True
