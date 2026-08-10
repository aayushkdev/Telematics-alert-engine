import asyncio
import json
import logging

import aio_pika
from pydantic import ValidationError

from app.core.config import settings
from app.db.session import SessionLocal
from app.messaging.rabbitmq import TELEMETRY_QUEUE
from app.schemas.telemetry import TelemetryCreate
from app.services import telemetry

logger = logging.getLogger(__name__)


async def process_message(message: aio_pika.IncomingMessage) -> None:
    try:
        data = TelemetryCreate.model_validate(json.loads(message.body))
        async with SessionLocal() as db:
            await telemetry.create(db, data)
    except telemetry.DuplicateEventError:
        logger.info("Ignoring duplicate telemetry event")
    except telemetry.VehicleNotFoundError:
        logger.error("Dropping telemetry for unknown vehicle")
    except (ValidationError, json.JSONDecodeError):
        logger.error("Dropping invalid telemetry message")
    except Exception:
        logger.exception("Telemetry processing failed; message will be retried")
        raise


async def run() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    queue = await channel.declare_queue(TELEMETRY_QUEUE, durable=True)
    logger.info("Telemetry worker listening on %s", TELEMETRY_QUEUE)

    async with queue.iterator() as messages:
        async for message in messages:
            try:
                async with message.process(requeue=True):
                    await process_message(message)
            except Exception:
                # Keep the worker alive; aio-pika will redeliver transient failures.
                await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
