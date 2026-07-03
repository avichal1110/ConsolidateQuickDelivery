"""
Generates a synthetic-but-realistic delivery order dataset matching the
schema expected by data.py. Used for evaluation since the original
100k-row dataset (delivery_massive_dataset_100k.csv) lives on a local
machine and isn't available here.

This mimics an evening peak-hour window (7:00 PM - 10:00 PM) across a
handful of Mumbai localities, with orders clustering around a few
restaurants per area (as real food-delivery demand does), plus a
deliberate demand ramp so LOW / MEDIUM / HIGH windows are all exercised.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

AREAS = ["Andheri East", "Andheri West", "Bandra West", "Powai", "Malad West"]
RESTAURANTS_PER_AREA = 4  # e.g. REST_A0..REST_A3 for Andheri East
WEATHER = ["Clear", "Rain", "Cloudy"]
TRAFFIC = ["Low", "Medium", "High"]
PAYMENT = ["UPI", "Card", "COD"]

START = datetime(2026, 7, 3, 19, 0, 0)  # 7:00 PM
TOTAL_MINUTES = 180  # 3-hour simulation window


def restaurant_ids_for_area(area_index):
    letter = chr(ord("A") + area_index)
    return [f"REST_{letter}{i}" for i in range(RESTAURANTS_PER_AREA)]


def demand_curve_orders_per_minute(minute):
    """Ramps LOW -> HIGH -> LOW to exercise all demand bands."""
    if minute < 45:
        return random.choice([0, 0, 1])          # LOW
    if minute < 120:
        return random.choice([1, 1, 2, 2, 3])     # MEDIUM/HIGH mix (peak)
    return random.choice([0, 1])                  # tapering back to LOW


def generate_rows():
    rows = []
    order_counter = 1

    for minute in range(TOTAL_MINUTES):
        n_orders = demand_curve_orders_per_minute(minute)
        for _ in range(n_orders):
            area_idx = random.randint(0, len(AREAS) - 1)
            area = AREAS[area_idx]
            restaurant_id = random.choice(restaurant_ids_for_area(area_idx))

            ts = START + timedelta(minutes=minute, seconds=random.randint(0, 59))
            prep_time = random.randint(8, 20)
            distance_km = round(random.uniform(0.8, 6.5), 2)
            travel_time = max(3, int(distance_km * random.uniform(3.0, 4.5)))
            eta = prep_time + travel_time
            sla = random.choice([30, 35, 40])

            row = {
                "order_id": f"ORD{order_counter:06d}",
                "timestamp": ts.isoformat(),
                "area": area,
                "restaurant_id": restaurant_id,
                "cust_lat": round(19.05 + random.uniform(-0.05, 0.05), 5),
                "cust_lon": round(72.86 + random.uniform(-0.05, 0.05), 5),
                "prep_time_min": prep_time,
                "items_count": random.randint(1, 5),
                "order_value": random.randint(150, 1200),
                "priority": random.choice(["Normal", "Normal", "High"]),
                "payment_mode": random.choice(PAYMENT),
                "riders_available": random.randint(2, 10),
                "avg_rider_distance_km": round(random.uniform(0.5, 3.0), 2),
                "vehicle_capacity": random.choice([1, 2, 3]),
                "traffic_level": random.choice(TRAFFIC),
                "weather": random.choice(WEATHER),
                "peak_hour": 1 if 30 <= minute <= 120 else 0,
                "pending_orders_area": random.randint(0, 12),
                "pending_orders_same_restaurant": random.randint(0, 5),
                "expected_new_orders_5min": random.randint(0, 6),
                "surge_multiplier": round(random.choice([1.0, 1.1, 1.25, 1.5]), 2),
                "distance_km": distance_km,
                "travel_time_min": travel_time,
                "ETA_min": eta,
                "SLA_min": sla,
                "SLA_remaining_min": sla - eta,
            }
            rows.append(row)
            order_counter += 1

    return rows


def main():
    rows = generate_rows()
    columns = list(rows[0].keys())

    out_path = "delivery_dataset.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} synthetic orders -> {out_path}")


if __name__ == "__main__":
    main()
