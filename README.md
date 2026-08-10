# MotorQ

Telematics alert engine built with FastAPI, PostgreSQL, Redis, and RabbitMQ.

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

## API Examples

### Create Organization

```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp"}'
```

### Create Vehicle

```bash
curl -X POST http://localhost:8000/api/v1/vehicles \
  -H "Content-Type: application/json" \
  -d '{"organization_id": 1, "vin": "VIN1234567890", "display_name": "Truck 01"}'
```

### Send Telemetry

```bash
curl -X POST http://localhost:8000/api/v1/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "event-001",
    "organization_id": 1,
    "vehicle_id": "VIN1234567890",
    "timestamp": "2026-08-03T10:45:00Z",
    "speed_mph": 65,
    "fuel_level_percent": 42,
    "engine_state": "on",
    "odometer_miles": 12050,
    "latitude": 12.9716,
    "longitude": 77.5946
  }'
```

**Response (HTTP 201):**

```json
{
  "id": 1,
  "event_id": "event-001",
  "organization_id": 1,
  "vehicle_id": "VIN1234567890",
  "timestamp": "2026-08-03T10:45:00Z",
  "speed_mph": 65,
  "fuel_level_percent": 42,
  "engine_state": "on",
  "odometer_miles": 12050,
  "latitude": 12.9716,
  "longitude": 77.5946,
  "received_at": "2026-08-10T23:30:00Z"
}
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

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/organizations | Create organization |
| GET | /api/v1/organizations/{id} | Get organization |
| PATCH | /api/v1/organizations/{id} | Update organization |
| POST | /api/v1/users | Create user |
| GET | /api/v1/users?organization_id= | List users |
| POST | /api/v1/drivers | Create driver |
| GET | /api/v1/drivers?organization_id= | List drivers |
| POST | /api/v1/vehicles | Create vehicle |
| GET | /api/v1/vehicles?organization_id= | List vehicles |
| POST | /api/v1/vehicles/{id}/assign-driver | Assign driver |
| POST | /api/v1/telemetry | Send telemetry |