import argparse
import asyncio
import math
import random
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx


@dataclass
class SimulatedVehicle:
    vin: str
    latitude: float
    longitude: float
    odometer_miles: float
    fuel_level_percent: float
    heading_degrees: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send simulated vehicle telemetry")
    parser.add_argument("--organization-id", type=int, required=True)
    parser.add_argument("--api-url", default="http://localhost:8000/api/v1")
    parser.add_argument("--vehicle-count", type=int, default=1)
    parser.add_argument("--vehicle-prefix", default="SIM")
    parser.add_argument(
        "--vehicle-ids",
        help="Comma-separated existing vehicle VINs; overrides --vehicle-count",
    )
    parser.add_argument("--create-vehicles", action="store_true")
    parser.add_argument("--scenario", choices=["normal", "speeding", "low-fuel", "mixed"], default="mixed")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--iterations", type=int, default=0, help="0 runs forever")
    parser.add_argument("--speed-mph", type=float, help="Fixed speed for every event")
    parser.add_argument("--latitude", type=float, default=12.9716)
    parser.add_argument("--longitude", type=float, default=77.5946)
    parser.add_argument("--seed", type=int)
    return parser.parse_args()


def vehicle_ids(args: argparse.Namespace) -> list[str]:
    if args.vehicle_ids:
        return [vehicle_id.strip() for vehicle_id in args.vehicle_ids.split(",") if vehicle_id.strip()]
    if not 1 <= args.vehicle_count <= 100:
        raise ValueError("vehicle-count must be between 1 and 100")
    return [f"{args.vehicle_prefix}-{index:04d}" for index in range(1, args.vehicle_count + 1)]


def build_vehicles(args: argparse.Namespace, rng: random.Random) -> list[SimulatedVehicle]:
    vehicles = []
    for index, vin in enumerate(vehicle_ids(args)):
        vehicles.append(
            SimulatedVehicle(
                vin=vin,
                latitude=args.latitude + (index * 0.001),
                longitude=args.longitude + (index * 0.001),
                odometer_miles=rng.uniform(10_000, 50_000),
                fuel_level_percent=rng.uniform(45, 90),
                heading_degrees=rng.uniform(0, 360),
            )
        )
    return vehicles


def scenario_for(index: int, requested_scenario: str) -> str:
    if requested_scenario != "mixed":
        return requested_scenario
    return ("normal", "speeding", "low-fuel")[index % 3]


def build_payload(
    vehicle: SimulatedVehicle,
    scenario: str,
    interval_seconds: float,
    rng: random.Random,
    speed_mph: float | None = None,
) -> dict:
    if speed_mph is None:
        if scenario == "speeding":
            speed_mph = rng.uniform(75, 90)
        elif scenario == "low-fuel":
            speed_mph = rng.uniform(25, 55)
            vehicle.fuel_level_percent = min(
                vehicle.fuel_level_percent, rng.uniform(5, 15)
            )
        else:
            speed_mph = rng.uniform(30, 60)

    distance_miles = speed_mph * interval_seconds / 3600
    heading = math.radians(vehicle.heading_degrees)
    vehicle.latitude = max(
        -89.9, min(89.9, vehicle.latitude + (distance_miles * math.cos(heading) / 69))
    )
    longitude_scale = max(0.01, 69 * math.cos(math.radians(vehicle.latitude)))
    vehicle.longitude = ((vehicle.longitude + (distance_miles * math.sin(heading) / longitude_scale) + 180) % 360) - 180
    vehicle.odometer_miles += distance_miles
    vehicle.fuel_level_percent = max(0, vehicle.fuel_level_percent - (distance_miles * 0.02))

    return {
        "event_id": str(uuid.uuid4()),
        "vehicle_id": vehicle.vin,
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "speed_mph": round(speed_mph, 2),
        "fuel_level_percent": round(vehicle.fuel_level_percent, 2),
        "engine_state": "on",
        "odometer_miles": round(vehicle.odometer_miles, 2),
        "latitude": round(vehicle.latitude, 6),
        "longitude": round(vehicle.longitude, 6),
    }


async def ensure_vehicles(
    client: httpx.AsyncClient, organization_id: int, vehicles: list[SimulatedVehicle]
) -> None:
    response = await client.get("/vehicles", params={"organization_id": organization_id})
    response.raise_for_status()
    existing_vins = {vehicle["vin"] for vehicle in response.json()}

    for vehicle in vehicles:
        if vehicle.vin in existing_vins:
            continue
        response = await client.post(
            "/vehicles",
            json={
                "organization_id": organization_id,
                "vin": vehicle.vin,
                "display_name": f"Simulator {vehicle.vin}",
            },
        )
        response.raise_for_status()


async def send_telemetry(
    client: httpx.AsyncClient, organization_id: int, payload: dict
) -> bool:
    response = await client.post(
        "/telemetry", json={"organization_id": organization_id, **payload}
    )
    if response.is_success:
        return True
    print(f"telemetry rejected for {payload['vehicle_id']}: {response.status_code} {response.text}")
    return False


async def run(args: argparse.Namespace) -> None:
    if args.interval <= 0:
        raise ValueError("interval must be greater than zero")
    if args.iterations < 0:
        raise ValueError("iterations must be zero or positive")
    if args.speed_mph is not None and args.speed_mph < 0:
        raise ValueError("speed-mph must be zero or positive")

    rng = random.Random(args.seed)
    vehicles = build_vehicles(args, rng)
    async with httpx.AsyncClient(base_url=args.api_url, timeout=10.0) as client:
        if args.create_vehicles:
            await ensure_vehicles(client, args.organization_id, vehicles)

        iteration = 0
        while args.iterations == 0 or iteration < args.iterations:
            started_at = time.monotonic()
            payloads = [
                build_payload(
                    vehicle,
                    scenario_for(index, args.scenario),
                    args.interval,
                    rng,
                    args.speed_mph,
                )
                for index, vehicle in enumerate(vehicles)
            ]
            results = await asyncio.gather(
                *(send_telemetry(client, args.organization_id, payload) for payload in payloads)
            )
            print(f"iteration {iteration + 1}: {sum(results)}/{len(results)} telemetry events accepted")
            iteration += 1

            if args.iterations == 0 or iteration < args.iterations:
                await asyncio.sleep(max(0, args.interval - (time.monotonic() - started_at)))


def main() -> None:
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
