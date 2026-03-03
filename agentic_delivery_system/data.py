"""Data loading utilities for the agentic delivery system."""

import csv
from pathlib import Path


DATA_COLUMNS = [
    "order_id",
    "timestamp",
    "area",
    "restaurant_id",
    "cust_lat",
    "cust_lon",
    "prep_time_min",
    "items_count",
    "order_value",
    "priority",
    "payment_mode",
    "riders_available",
    "avg_rider_distance_km",
    "vehicle_capacity",
    "traffic_level",
    "weather",
    "peak_hour",
    "pending_orders_area",
    "pending_orders_same_restaurant",
    "expected_new_orders_5min",
    "surge_multiplier",
    "distance_km",
    "travel_time_min",
    "ETA_min",
    "SLA_min",
    "SLA_remaining_min",
]

INT_COLUMNS = {
    "prep_time_min",
    "items_count",
    "order_value",
    "riders_available",
    "vehicle_capacity",
    "peak_hour",
    "pending_orders_area",
    "pending_orders_same_restaurant",
    "expected_new_orders_5min",
    "travel_time_min",
    "ETA_min",
    "SLA_min",
    "SLA_remaining_min",
}

FLOAT_COLUMNS = {
    "cust_lat",
    "cust_lon",
    "avg_rider_distance_km",
    "surge_multiplier",
    "distance_km",
}

REQUIRED_COLUMNS = {"order_id", "timestamp", "area", "restaurant_id"}

DEFAULT_DATASET_PATH = Path(
    r"C:\Users\Achint Kumar\Downloads\delivery_massive_dataset_100k.csv"
)


def _parse_value(column, value):
    text = "" if value is None else str(value).strip()

    if column in REQUIRED_COLUMNS and text == "":
        raise ValueError(f"Missing required value for '{column}'")

    if text == "":
        if column in INT_COLUMNS:
            return 0
        if column in FLOAT_COLUMNS:
            return 0.0
        return ""

    if column in INT_COLUMNS:
        return int(float(text))

    if column in FLOAT_COLUMNS:
        return float(text)

    return text


def _normalize_row(raw_row):
    return {column: _parse_value(column, raw_row.get(column)) for column in DATA_COLUMNS}


def _has_header(first_line):
    expected = ",".join(DATA_COLUMNS)
    return first_line.strip().lower() == expected.lower()


def get_orders(csv_path=None, limit=None):
    """
    Load orders from CSV with the expected schema.

    Args:
    - csv_path: optional path to CSV; defaults to Downloads dataset path.
    - limit: optional row cap for quick tests.
    """
    path = Path(csv_path) if csv_path else DEFAULT_DATASET_PATH

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        first_line = handle.readline()

    header_present = _has_header(first_line)
    orders = []
    skipped_rows = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        if header_present:
            reader = csv.DictReader(handle)
            missing_columns = [c for c in DATA_COLUMNS if c not in (reader.fieldnames or [])]
            if missing_columns:
                raise ValueError(f"CSV missing required columns: {missing_columns}")
        else:
            reader = csv.DictReader(handle, fieldnames=DATA_COLUMNS)

        for raw in reader:
            try:
                orders.append(_normalize_row(raw))
            except (TypeError, ValueError):
                skipped_rows += 1
                continue

            if limit is not None and len(orders) >= limit:
                break

    if not orders:
        raise ValueError("No valid orders were loaded from CSV.")

    if skipped_rows:
        print(f"Skipped {skipped_rows} malformed rows while loading data.")

    return orders


def get_synthetic_orders():
    """Backward-compatible alias now loading real CSV orders."""
    return get_orders()
