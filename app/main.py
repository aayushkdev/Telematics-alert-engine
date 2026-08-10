from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.redis import close_client
from app.messaging.rabbitmq import close as close_rabbitmq
from app.routes import (
    alerts,
    drivers,
    health,
    organizations,
    rules,
    telemetry,
    users,
    vehicles,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_client()
    await close_rabbitmq()


app = FastAPI(
    title="MotorQ API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(
    organizations.router, prefix="/api/v1/organizations", tags=["organizations"]
)
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(drivers.router, prefix="/api/v1/drivers", tags=["drivers"])
app.include_router(vehicles.router, prefix="/api/v1/vehicles", tags=["vehicles"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["rules"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True)
