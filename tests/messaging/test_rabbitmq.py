import json

import pytest

from app.messaging import rabbitmq


class FakeExchange:
    def __init__(self):
        self.message = None
        self.routing_key = None

    async def publish(self, message, routing_key):
        self.message = message
        self.routing_key = routing_key


class FakeChannel:
    def __init__(self):
        self.default_exchange = FakeExchange()


@pytest.mark.asyncio
async def test_publish_telemetry_sends_json_to_durable_queue(monkeypatch):
    channel = FakeChannel()

    async def fake_channel():
        return channel

    monkeypatch.setattr(rabbitmq, "_channel_for_publish", fake_channel)

    await rabbitmq.publish_telemetry({"event_id": "evt-1", "speed_mph": 80})

    assert channel.default_exchange.routing_key == rabbitmq.TELEMETRY_QUEUE
    assert json.loads(channel.default_exchange.message.body) == {
        "event_id": "evt-1",
        "speed_mph": 80,
    }
