from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="MotorQ API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, prefix="/health", tags=["health"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)