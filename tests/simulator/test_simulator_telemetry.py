import argparse
import random

from simulator.telemetry import build_payload, build_vehicles, scenario_for


def make_args(**changes):
    values = {
        "vehicle_ids": None,
        "vehicle_count": 2,
        "vehicle_prefix": "SIM",
        "latitude": 12.9716,
        "longitude": 77.5946,
    }
    values.update(changes)
    return argparse.Namespace(**values)


def test_simulator_generates_configured_vehicle_ids():
    vehicles = build_vehicles(make_args(vehicle_count=2), random.Random(1))

    assert [vehicle.vin for vehicle in vehicles] == ["SIM-0001", "SIM-0002"]


def test_simulator_payload_moves_vehicle_and_includes_coordinates():
    vehicle = build_vehicles(make_args(vehicle_count=1), random.Random(1))[0]
    original_coordinates = (vehicle.latitude, vehicle.longitude)

    payload = build_payload(vehicle, "speeding", 60, random.Random(2))

    assert payload["vehicle_id"] == "SIM-0001"
    assert payload["speed_mph"] > 70
    assert payload["latitude"] != original_coordinates[0]
    assert payload["longitude"] != original_coordinates[1]
    assert payload["engine_state"] == "on"


def test_mixed_scenario_assigns_normal_speeding_and_low_fuel():
    assert [scenario_for(index, "mixed") for index in range(3)] == [
        "normal",
        "speeding",
        "low-fuel",
    ]


def test_fixed_speed_overrides_scenario_speed():
    vehicle = build_vehicles(make_args(vehicle_count=1), random.Random(1))[0]

    payload = build_payload(vehicle, "normal", 1, random.Random(2), speed_mph=105)

    assert payload["speed_mph"] == 105
