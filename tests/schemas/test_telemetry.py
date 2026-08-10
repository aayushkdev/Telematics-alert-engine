import pytest
from pydantic import ValidationError

from app.schemas.telemetry import TelemetryCreate


def test_latitude_below_range():
    with pytest.raises(ValidationError) as exc:
        TelemetryCreate(
            event_id="test",
            organization_id=1,
            vehicle_id="VIN123",
            timestamp="2026-08-03T10:45:00Z",
            latitude=-91,
            longitude=0,
        )
    assert "latitude" in str(exc.value)


def test_latitude_above_range():
    with pytest.raises(ValidationError) as exc:
        TelemetryCreate(
            event_id="test",
            organization_id=1,
            vehicle_id="VIN123",
            timestamp="2026-08-03T10:45:00Z",
            latitude=91,
            longitude=0,
        )
    assert "latitude" in str(exc.value)


def test_longitude_below_range():
    with pytest.raises(ValidationError) as exc:
        TelemetryCreate(
            event_id="test",
            organization_id=1,
            vehicle_id="VIN123",
            timestamp="2026-08-03T10:45:00Z",
            latitude=0,
            longitude=-181,
        )
    assert "longitude" in str(exc.value)


def test_longitude_above_range():
    with pytest.raises(ValidationError) as exc:
        TelemetryCreate(
            event_id="test",
            organization_id=1,
            vehicle_id="VIN123",
            timestamp="2026-08-03T10:45:00Z",
            latitude=0,
            longitude=181,
        )
    assert "longitude" in str(exc.value)


def test_latitude_provided_but_longitude_null():
    with pytest.raises(ValidationError) as exc:
        TelemetryCreate(
            event_id="test",
            organization_id=1,
            vehicle_id="VIN123",
            timestamp="2026-08-03T10:45:00Z",
            latitude=12.97,
            longitude=None,
        )
    assert "latitude and longitude" in str(exc.value)


def test_longitude_provided_but_latitude_null():
    with pytest.raises(ValidationError) as exc:
        TelemetryCreate(
            event_id="test",
            organization_id=1,
            vehicle_id="VIN123",
            timestamp="2026-08-03T10:45:00Z",
            latitude=None,
            longitude=77.59,
        )
    assert "latitude and longitude" in str(exc.value)


def test_both_coordinates_null_valid():
    t = TelemetryCreate(
        event_id="test",
        organization_id=1,
        vehicle_id="VIN123",
        timestamp="2026-08-03T10:45:00Z",
        latitude=None,
        longitude=None,
    )
    assert t.latitude is None
    assert t.longitude is None


def test_both_coordinates_provided_valid():
    t = TelemetryCreate(
        event_id="test",
        organization_id=1,
        vehicle_id="VIN123",
        timestamp="2026-08-03T10:45:00Z",
        latitude=12.9716,
        longitude=77.5946,
    )
    assert t.latitude == 12.9716
    assert t.longitude == 77.5946
