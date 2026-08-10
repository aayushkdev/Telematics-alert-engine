from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from redis.exceptions import RedisError

from app.services import windowing


class FakePipeline:
    def __init__(self, client):
        self.client = client
        self.commands = []

    def zadd(self, key, values):
        self.commands.append(("zadd", key, values))
        return self

    def zremrangebyscore(self, key, minimum, maximum):
        self.commands.append(("zremrangebyscore", key, minimum, maximum))
        return self

    def zcount(self, key, minimum, maximum):
        self.commands.append(("zcount", key, minimum, maximum))
        return self

    def expire(self, key, seconds):
        self.commands.append(("expire", key, seconds))
        return self

    async def execute(self):
        results = []
        for command, key, *args in self.commands:
            events = self.client.events.setdefault(key, {})
            if command == "zadd":
                member, score = next(iter(args[0].items()))
                added = int(member not in events)
                events[member] = score
                results.append(added)
            elif command == "zremrangebyscore":
                cutoff = float(args[1][1:])
                expired = [member for member, score in events.items() if score < cutoff]
                for member in expired:
                    del events[member]
                results.append(len(expired))
            elif command == "zcount":
                cutoff = float(args[0])
                results.append(sum(score >= cutoff for score in events.values()))
            else:
                self.client.expirations[key] = args[0]
                results.append(True)
        return results


class FakeRedis:
    def __init__(self):
        self.events = {}
        self.expirations = {}

    def pipeline(self, transaction):
        assert transaction is True
        return FakePipeline(self)


def make_rule(window_seconds=120, min_matching_events=3):
    rule = MagicMock()
    rule.id = 7
    rule.window_seconds = window_seconds
    rule.min_matching_events = min_matching_events
    return rule


def make_telemetry(event_id, seconds):
    telemetry = MagicMock()
    telemetry.event_id = event_id
    telemetry.vehicle_id = 12
    telemetry.timestamp = datetime(2026, 8, 11, tzinfo=UTC) + timedelta(
        seconds=seconds
    )
    return telemetry


@pytest.mark.asyncio
async def test_events_inside_window_trigger_at_minimum(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(windowing.redis, "get_client", lambda: client)
    rule = make_rule()

    assert await windowing.threshold_reached(rule, make_telemetry("one", 0)) is False
    assert await windowing.threshold_reached(rule, make_telemetry("two", 30)) is False
    assert await windowing.threshold_reached(rule, make_telemetry("three", 100)) is True


@pytest.mark.asyncio
async def test_events_outside_window_do_not_count(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(windowing.redis, "get_client", lambda: client)
    rule = make_rule()

    assert await windowing.threshold_reached(rule, make_telemetry("one", 0)) is False
    assert await windowing.threshold_reached(rule, make_telemetry("two", 60)) is False
    assert await windowing.threshold_reached(rule, make_telemetry("three", 121)) is False


@pytest.mark.asyncio
async def test_event_on_window_boundary_counts(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(windowing.redis, "get_client", lambda: client)
    rule = make_rule()

    assert await windowing.threshold_reached(rule, make_telemetry("one", 0)) is False
    assert await windowing.threshold_reached(rule, make_telemetry("two", 60)) is False
    assert await windowing.threshold_reached(rule, make_telemetry("three", 120)) is True


@pytest.mark.asyncio
async def test_repeated_event_id_is_counted_once(monkeypatch):
    client = FakeRedis()
    monkeypatch.setattr(windowing.redis, "get_client", lambda: client)
    rule = make_rule(min_matching_events=2)

    assert await windowing.threshold_reached(rule, make_telemetry("same", 0)) is False
    assert await windowing.threshold_reached(rule, make_telemetry("same", 10)) is False


@pytest.mark.asyncio
async def test_redis_failure_does_not_trigger_windowed_alert(monkeypatch):
    client = MagicMock()
    client.pipeline.side_effect = RedisError("unavailable")
    monkeypatch.setattr(windowing.redis, "get_client", lambda: client)

    assert await windowing.threshold_reached(make_rule(), make_telemetry("one", 0)) is False
