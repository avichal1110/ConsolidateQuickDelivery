"""
DemandAgent: estimates demand level from recent order volume.
"""

from datetime import datetime


class DemandAgent:
    """
    Rule-based demand estimator.

    Logic:
    - Count number of orders in a recent time window.
    - Map count to demand labels: LOW, MEDIUM, HIGH.
    """

    def __init__(self, window_minutes=10, low_threshold=3, high_threshold=7):
        """
        Parameters:
        - window_minutes: recent time horizon for demand check
        - low_threshold: max count for LOW
        - high_threshold: min count for HIGH
          (counts between low_threshold+1 and high_threshold-1 => MEDIUM)
        """
        self.window_minutes = window_minutes
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def _minute_value(self, order):
        """
        Return order time as minutes from midnight.

        Supports current schema key `timestamp` and legacy key `time`.
        """
        ts = order.get("timestamp")
        if ts is not None:
            if isinstance(ts, (int, float)):
                return int(ts)
            dt = datetime.fromisoformat(str(ts))
            return dt.hour * 60 + dt.minute

        if "time" in order:
            return int(order["time"])

        raise KeyError("Order must contain 'timestamp' or 'time'.")

    def assess_demand(self, orders):
        """
        Assess demand level using the most recent window.

        Steps:
        1. Find latest order time.
        2. Keep orders within [latest_time - window_minutes, latest_time].
        3. Count recent orders and convert to LOW/MEDIUM/HIGH.

        Returns:
        - demand_level: str
        - recent_count: int
        - window_start: int (minutes from midnight)
        - window_end: int (minutes from midnight)
        """
        if not orders:
            return "LOW", 0, 0, 0

        minute_values = [self._minute_value(order) for order in orders]
        latest_time = max(minute_values)
        window_start = latest_time - self.window_minutes

        recent_count = sum(
            1
            for order in orders
            if window_start <= self._minute_value(order) <= latest_time
        )

        if recent_count <= self.low_threshold:
            demand_level = "LOW"
        elif recent_count >= self.high_threshold:
            demand_level = "HIGH"
        else:
            demand_level = "MEDIUM"

        return demand_level, recent_count, window_start, latest_time
