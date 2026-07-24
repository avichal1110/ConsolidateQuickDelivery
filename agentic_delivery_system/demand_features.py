"""
Builds a windowed feature table from raw orders and trains a model to
forecast order volume in the NEXT 5-minute window, using only information
available up to the current window (no leakage from the future).

This is what MLDemandAgent (ml_demand_agent.py) trains on. Kept as a
separate module so the feature engineering can be inspected/reused
independently of the agent wrapper.
"""

from datetime import datetime
import pandas as pd
import numpy as np

WINDOW_MINUTES = 5

TRAFFIC_ENCODING = {"Low": 0, "Medium": 1, "High": 2}


def _minute_value(order):
    ts = order.get("timestamp")
    if isinstance(ts, (int, float)):
        return int(ts)
    dt = datetime.fromisoformat(str(ts))
    return dt.hour * 60 + dt.minute


def build_window_table(orders, window_minutes=WINDOW_MINUTES):
    """
    Bins orders into fixed windows and returns a DataFrame with one row
    per window: order_count plus contextual features averaged over the
    orders that fell in that window.
    """
    rows = []
    for order in orders:
        minute = _minute_value(order)
        rows.append(
            {
                "minute": minute,
                "window": minute // window_minutes,
                "traffic": TRAFFIC_ENCODING.get(order.get("traffic_level"), 1),
                "surge": float(order.get("surge_multiplier", 1.0) or 1.0),
                "riders_available": float(order.get("riders_available", 0) or 0),
                "pending_orders_area": float(order.get("pending_orders_area", 0) or 0),
                "expected_new_orders_5min": float(order.get("expected_new_orders_5min", 0) or 0),
                "peak_hour": int(order.get("peak_hour", 0) or 0),
            }
        )

    df = pd.DataFrame(rows)

    grouped = df.groupby("window").agg(
        order_count=("minute", "count"),
        avg_traffic=("traffic", "mean"),
        avg_surge=("surge", "mean"),
        avg_riders_available=("riders_available", "mean"),
        avg_pending_orders_area=("pending_orders_area", "mean"),
        avg_expected_new_orders_5min=("expected_new_orders_5min", "mean"),
        peak_hour=("peak_hour", "max"),
    ).reset_index()

    # Fill any windows with zero orders (gaps) so lags stay meaningful
    full_range = pd.DataFrame({"window": range(grouped["window"].min(), grouped["window"].max() + 1)})
    grouped = full_range.merge(grouped, on="window", how="left")
    grouped["order_count"] = grouped["order_count"].fillna(0)
    grouped = grouped.ffill().fillna(0)

    # Lag features: what we knew *before* this window started
    grouped["lag1_count"] = grouped["order_count"].shift(1).fillna(0)
    grouped["lag2_count"] = grouped["order_count"].shift(2).fillna(0)

    # Target: next window's order count (what we're forecasting)
    grouped["target_next_count"] = grouped["order_count"].shift(-1)

    return grouped.dropna(subset=["target_next_count"]).reset_index(drop=True)


FEATURE_COLUMNS = [
    "order_count", "lag1_count", "lag2_count",
    "avg_traffic", "avg_surge", "avg_riders_available",
    "avg_pending_orders_area", "avg_expected_new_orders_5min", "peak_hour",
]
