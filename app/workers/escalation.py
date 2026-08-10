import asyncio
import logging

from app.db.session import SessionLocal
from app.services import alert

logger = logging.getLogger(__name__)
INTERVAL_SECONDS = 60


async def run() -> None:
    while True:
        try:
            async with SessionLocal() as db:
                escalated = await alert.escalate_overdue(db)
                if escalated:
                    logger.info("Escalated %s alert(s)", escalated)
        except Exception:
            logger.exception("Alert escalation cycle failed")

        await asyncio.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
