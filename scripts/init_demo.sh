#!/usr/bin/env bash

set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_command curl
require_command jq

post() {
  curl --fail --silent --show-error -X POST "$API_URL/$1" \
    -H "Content-Type: application/json" \
    -d "$2"
}

ORG_ID=$(post organizations '{"name":"Simulator Demo Org"}' | jq -r '.id')

DRIVER_1=$(post drivers "{\"organization_id\":$ORG_ID,\"name\":\"Aarav Sharma\",\"phone\":\"+919900000001\"}" | jq -r '.id')
DRIVER_2=$(post drivers "{\"organization_id\":$ORG_ID,\"name\":\"Meera Iyer\",\"phone\":\"+919900000002\"}" | jq -r '.id')

RUN_SUFFIX=$(date +%s)
VIN_1="SIM${RUN_SUFFIX}01"
VIN_2="SIM${RUN_SUFFIX}02"
VIN_3="SIM${RUN_SUFFIX}03"

VEHICLE_1=$(post vehicles "{\"organization_id\":$ORG_ID,\"vin\":\"$VIN_1\",\"display_name\":\"Demo Truck 1\"}" | jq -r '.id')
VEHICLE_2=$(post vehicles "{\"organization_id\":$ORG_ID,\"vin\":\"$VIN_2\",\"display_name\":\"Demo Truck 2\"}" | jq -r '.id')
VEHICLE_3=$(post vehicles "{\"organization_id\":$ORG_ID,\"vin\":\"$VIN_3\",\"display_name\":\"Demo Truck 3\"}" | jq -r '.id')

post "vehicles/$VEHICLE_1/assign-driver?organization_id=$ORG_ID" "{\"driver_id\":$DRIVER_1}" >/dev/null
post "vehicles/$VEHICLE_2/assign-driver?organization_id=$ORG_ID" "{\"driver_id\":$DRIVER_2}" >/dev/null

LOW_FUEL_RULE=$(post rules "{\"organization_id\":$ORG_ID,\"name\":\"Low fuel below 10 percent\",\"rule_type\":\"simple\",\"field\":\"fuel_level_percent\",\"operator\":\"<\",\"threshold\":10,\"suppress_for_seconds\":300,\"escalate_after_seconds\":900}" | jq -r '.id')
SPEED_RULE=$(post rules "{\"organization_id\":$ORG_ID,\"vehicle_id\":$VEHICLE_1,\"name\":\"Speed above 100 mph for 5 seconds\",\"rule_type\":\"windowed\",\"field\":\"speed_mph\",\"operator\":\">\",\"threshold\":100,\"window_seconds\":5,\"min_matching_events\":6}" | jq -r '.id')
ODOMETER_RULE=$(post rules "{\"organization_id\":$ORG_ID,\"name\":\"Odometer above 50000 miles\",\"rule_type\":\"simple\",\"field\":\"odometer_miles\",\"operator\":\">\",\"threshold\":50000,\"suppress_for_seconds\":3600}" | jq -r '.id')
GEOFENCE_RULE=$(post rules "{\"organization_id\":$ORG_ID,\"vehicle_id\":$VEHICLE_1,\"name\":\"Outside simulator radius\",\"rule_type\":\"simple\",\"field\":\"location\",\"operator\":\"outside_radius\",\"threshold\":0.1,\"center_latitude\":12.9716,\"center_longitude\":77.5946,\"suppress_for_seconds\":60}" | jq -r '.id')

cat <<EOF
Demo data created.

ORG_ID=$ORG_ID
DRIVER_1=$DRIVER_1
DRIVER_2=$DRIVER_2
VEHICLE_1=$VEHICLE_1  VIN_1=$VIN_1
VEHICLE_2=$VEHICLE_2  VIN_2=$VIN_2
VEHICLE_3=$VEHICLE_3  VIN_3=$VIN_3
LOW_FUEL_RULE=$LOW_FUEL_RULE
SPEED_RULE=$SPEED_RULE
ODOMETER_RULE=$ODOMETER_RULE
GEOFENCE_RULE=$GEOFENCE_RULE

Run the speeding simulator with:
uv run --group dev python -m simulator.telemetry --organization-id $ORG_ID --vehicle-ids $VIN_1 --speed-mph 105 --interval 1 --iterations 6
EOF

cat > /tmp/motorq-demo.fish <<EOF
set -gx ORG_ID $ORG_ID
set -gx VIN_1 $VIN_1
set -gx VIN_2 $VIN_2
set -gx VIN_3 $VIN_3
EOF

echo "For Fish: source /tmp/motorq-demo.fish"
