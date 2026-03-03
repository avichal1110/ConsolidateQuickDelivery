"""
ConsolidationAgent: groups compatible orders for clubbed delivery.
"""

from datetime import datetime


class ConsolidationAgent:
    """
    Rule-based order consolidation.

    Orders can be clustered together if:
    - same area
    - same restaurant_id
    - within a 5-minute window from the first order in that cluster
    """

    def __init__(self, consolidation_window=5):
        self.consolidation_window = consolidation_window

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

    def _restaurant_key(self, order):
        """Support current key `restaurant_id` with backward compatibility."""
        if "restaurant_id" in order:
            return order["restaurant_id"]
        if "restaurant" in order:
            return order["restaurant"]
        raise KeyError("Order must contain 'restaurant_id' or 'restaurant'.")

    def consolidate(self, orders):
        """
        Group orders into clusters based on simple rules.

        Returns a list of clusters where each cluster is a dict:
        - cluster_id
        - area
        - restaurant_id
        - start_time
        - end_time
        - orders (list of order dicts)
        """
        if not orders:
            return []

        sorted_orders = sorted(
            orders,
            key=lambda x: (x["area"], self._restaurant_key(x), self._minute_value(x)),
        )

        clusters = []
        cluster_counter = 1

        for order in sorted_orders:
            order_time = self._minute_value(order)
            order_restaurant = self._restaurant_key(order)
            placed = False

            for cluster in clusters:
                same_area = cluster["area"] == order["area"]
                same_restaurant = cluster["restaurant_id"] == order_restaurant
                within_window = order_time - cluster["start_time"] <= self.consolidation_window

                if same_area and same_restaurant and within_window:
                    cluster["orders"].append(order)
                    cluster["end_time"] = max(cluster["end_time"], order_time)
                    placed = True
                    break

            if not placed:
                clusters.append(
                    {
                        "cluster_id": f"C{cluster_counter}",
                        "area": order["area"],
                        "restaurant_id": order_restaurant,
                        "start_time": order_time,
                        "end_time": order_time,
                        "orders": [order],
                    }
                )
                cluster_counter += 1

        return clusters
