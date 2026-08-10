from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes import health, organizations, users, drivers, vehicles


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="MotorQ API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(drivers.router, prefix="/api/v1/drivers", tags=["drivers"])
app.include_router(vehicles.router, prefix="/api/v1/vehicles", tags=["vehicles"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)