# MotorQ

FastAPI project with PostgreSQL, Redis, and RabbitMQ.

## Setup

```bash
# Start services
docker compose up -d

# Install dependencies
uv sync

# Run migrations
uv run alembic upgrade head

# Run server
uv run uvicorn app.main:app --reload
```

## Commands

```bash
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```