import json
from typing import Any

import aio_pika
from aio_pika import DeliveryMode, Message

from app.core.config import settings

TELEMETRY_QUEUE = "telemetry"

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.abc.AbstractRobustChannel | None = None


class MessagingUnavailable(Exception):
    """Raised when telemetry cannot be handed to RabbitMQ."""


async def _channel_for_publish() -> aio_pika.abc.AbstractRobustChannel:
    global _connection, _channel
    try:
        if _connection is None or _connection.is_closed:
            _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            _channel = None
        if _channel is None or _channel.is_closed:
            _channel = await _connection.channel(publisher_confirms=True)
            await _channel.declare_queue(TELEMETRY_QUEUE, durable=True)
        return _channel
    except Exception as exc:
        raise MessagingUnavailable from exc


async def publish_telemetry(payload: dict[str, Any]) -> None:
    channel = await _channel_for_publish()
    try:
        await channel.default_exchange.publish(
            Message(
                json.dumps(payload).encode(),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=TELEMETRY_QUEUE,
        )
    except Exception as exc:
        raise MessagingUnavailable from exc


async def close() -> None:
    global _connection, _channel
    if _connection is not None and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
