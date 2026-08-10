# MotorQ Telematics Alert Engine

## Goal

Receive vehicle telemetry, configure rules, and later evaluate them into alerts. The current implementation deliberately stays small: one FastAPI application and PostgreSQL. RabbitMQ and Redis are planned additions, not active parts of the current request path.

## Architecture

```text
Simulator / vehicle
        |
        | POST /api/v1/telemetry
        v
    FastAPI API
        |
        v
   Telemetry service
        |
        v
    PostgreSQL
```

### Responsibilities

| Component | Responsibility |
| --- | --- |
| FastAPI | Validate requests and expose management APIs. |
| Telemetry service | Resolve a VIN to a vehicle, save telemetry, and later evaluate rules. |
| PostgreSQL | Source of truth for organizations, vehicles, drivers, telemetry, rules, and alerts. |
| Simulator | Sends realistic, repeatable telemetry to the API for demos and tests. |

Later, FastAPI can publish telemetry to RabbitMQ and a worker can call the same telemetry service. Redis will hold only window and suppression state. There is no outbox and no microservice split.

## Domain model

```text
Organization
 ├─ Users
 ├─ Drivers
 ├─ Vehicles
 │   └─ current driver (optional)
 ├─ Rules
 └─ Alerts
```

### Main entities

| Entity | Important fields |
| --- | --- |
| Organization | `id`, `name`, `created_at` |
| User | `organization_id`, `name`, `email`, `role` |
| Driver | `organization_id`, `name`, `phone` |
| Vehicle | `organization_id`, `current_driver_id`, `vin`, `display_name` |
| Telemetry | `event_id`, `organization_id`, `vehicle_id`, timestamp, vehicle measurements, latitude, longitude |
| Rule | organization scope, optional vehicle scope, condition, suppression, escalation |
| Alert | rule, vehicle, optional driver snapshot, status, timestamps, occurrence count |

User roles are `admin`, `operator`, and `supervisor`.

There are intentionally no fleets. Organization-wide rules apply to all organization vehicles; a rule with `vehicle_id` applies to just that vehicle.

## Telemetry contract

```json
{
  "event_id": "b776a0d7-b893-4a51-9c6c-75f47a3a1fc4",
  "organization_id": 1,
  "vehicle_id": "VIN1234567890",
  "timestamp": "2026-08-03T10:45:00Z",
  "speed_mph": 65,
  "fuel_level_percent": 42,
  "engine_state": "on",
  "odometer_miles": 12050,
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

`event_id` is unique. PostgreSQL enforces this uniqueness, so duplicate requests cannot store the same telemetry twice. `vehicle_id` is the vehicle's alphanumeric VIN from the public API; the telemetry service resolves it to the internal integer `vehicles.id` before saving telemetry.

The current telemetry endpoint writes directly to PostgreSQL and responds with `201 Created`. When RabbitMQ is added later, the endpoint will respond with `202 Accepted` after publishing a durable message.

## Rules

Rules use a small fixed DSL; users never write Python or SQL.

Supported numeric fields in the first version:

```text
speed_mph
fuel_level_percent
odometer_miles
```

Supported operators:

```text
>
>=
<
<=
==
```

### Simple rule

```json
{
  "name": "Speeding",
  "rule_type": "simple",
  "field": "speed_mph",
  "operator": ">",
  "threshold": 70,
  "suppress_for_seconds": 600,
  "escalate_after_seconds": 900
}
```

The condition is evaluated against each telemetry event. The worker uses an explicit operator map, never `eval()`.

### Windowed rule (later)

```json
{
  "name": "Repeated speeding",
  "rule_type": "windowed",
  "field": "speed_mph",
  "operator": ">",
  "threshold": 70,
  "window_seconds": 300,
  "min_matching_events": 3,
  "suppress_for_seconds": 900,
  "escalate_after_seconds": 1800
}
```

This triggers when the vehicle exceeds 70 mph three times within five minutes.

Windowed evaluation is not implemented yet. It will use Redis sorted sets:

```text
window:{rule_id}:{vehicle_id}
```

For every matching event, the worker adds the timestamp, removes timestamps outside the window, counts what remains, and triggers if the count reaches `min_matching_events`. The key expires shortly after the window ends.

## Alert lifecycle

```text
OPEN -> ACKNOWLEDGED -> RESOLVED
  |
  +-> ESCALATED -> ACKNOWLEDGED or RESOLVED
```

When a rule matches:

1. Find an unresolved alert for the same rule and vehicle.
2. If one exists, update `occurrence_count` and `last_seen_at`.
3. If none exists and the rule is not currently suppressed, create an `OPEN` alert.

This ensures repeated low-fuel pings update one alert instead of creating hundreds.

### Suppression

When an alert is opened, set:

```text
suppress:{rule_id}:{vehicle_id}
```

Its TTL is `suppress_for_seconds`. If an alert was resolved but the condition immediately reappears, the suppression key prevents a duplicate alert until the TTL expires.

### Escalation

The scheduler runs once per minute:

```text
Find OPEN alerts where now - opened_at >= escalate_after_seconds.
```

It changes the alert to `ESCALATED`. Acknowledged alerts do not escalate.

This project is backend only. Alerts are exposed as API resources; there is no dashboard, email, SMS, or notification worker in scope.

## APIs

```text
GET    /health

POST   /api/v1/telemetry

POST   /api/v1/organizations
GET    /api/v1/organizations/{organization_id}

POST   /api/v1/users
POST   /api/v1/drivers
POST   /api/v1/vehicles
POST   /api/v1/vehicles/{vehicle_id}/assign-driver

POST   /api/v1/rules
GET    /api/v1/rules
GET    /api/v1/rules/{rule_id}
PATCH  /api/v1/rules/{rule_id}
DELETE /api/v1/rules/{rule_id}

GET    /api/v1/alerts
POST   /api/v1/alerts/{alert_id}/acknowledge
POST   /api/v1/alerts/{alert_id}/resolve
```

Authentication can be added later. Until then, each route must explicitly query using `organization_id` so one organization cannot access another organization's entities.

## Project layout

```text
app/
  core/          # settings and shared application concerns
  db/            # SQLAlchemy session and Alembic base
  models/        # database models and enums
  schemas/       # request/response validation models
  routes/        # FastAPI endpoints
  services/      # rule and alert business logic
  messaging/     # RabbitMQ connection and publishers (later)
  workers/       # telemetry and scheduler processes (later)

tests/
  routes/
  services/
  workers/
  integration/

simulator/
```

## Scaling approach

- FastAPI is stateless and can run multiple replicas.
- Add telemetry-worker replicas when RabbitMQ is introduced and the queue grows.
- Use unique `event_id` to make duplicate message delivery safe.
- Cache active rules in each worker instead of querying every rule for every ping.
- Redis keys must always have TTLs.
- Add time partitioning to the telemetry table only when its size requires it.
- If strict ordering per vehicle becomes necessary, shard RabbitMQ queues using a stable hash of `vehicle_id`.

## Build plan

1. Foundation: FastAPI, Docker Compose, SQLAlchemy, Alembic, health check.
2. Organization domain: organizations, users, drivers, vehicles, initial migration, and basic CRUD APIs.
3. Telemetry ingestion: validate `POST /api/v1/telemetry`, store it directly in PostgreSQL, and make duplicate `event_id` values safe.
4. Rule management: create, list, update, and delete organization-wide or vehicle-specific simple threshold rules. No evaluation yet.
5. Simple rule evaluation: evaluate configured rules after telemetry is saved.
6. Alerts: create one active alert per rule and vehicle; add list, acknowledge, and resolve APIs.
7. Suppression and escalation: Redis suppression keys and a scheduler that changes overdue unacknowledged alerts to `ESCALATED`.
8. Windowed rules: Redis sorted sets for “N matching events in X seconds”.
9. Simulator and tests: send normal, speeding, and low-fuel telemetry; add integration coverage and README commands.
