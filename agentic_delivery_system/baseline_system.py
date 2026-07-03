"""
BaselineSystem: represents naive/status-quo delivery operations, used as
a control to measure the value added by the agentic pipeline.

Rules (deliberately simple, mirroring an un-optimized dispatch process):
- No demand-aware waiting: every order is dispatched the moment it arrives.
- No consolidation: every order is its own "cluster" of size 1.
- No rider reuse across time: a fresh rider is assigned to every order.

This is the fairest apples-to-apples baseline because it uses the same
input data and the same service-time estimation logic as the agentic
DeliveryAgent, differing only in the *decisions* being compared.
"""


class BaselineSystem:
    def run(self, orders):
        clusters = [
            {
                "cluster_id": f"B{i + 1}",
                "area": order["area"],
                "restaurant_id": order.get("restaurant_id", order.get("restaurant")),
                "start_time": self._minute_value(order),
                "end_time": self._minute_value(order),
                "orders": [order],
            }
            for i, order in enumerate(orders)
        ]

        assignments = []
        for i, cluster in enumerate(clusters):
            order = cluster["orders"][0]
            eta = int(order.get("ETA_min", 0) or 0)
            travel = int(order.get("travel_time_min", 0) or 0)
            prep = int(order.get("prep_time_min", 0) or 0)
            service_time = max(1, eta, travel + prep)

            assignments.append(
                {
                    "rider_id": f"BR{i + 1}",  # every order gets its own rider
                    "cluster_id": cluster["cluster_id"],
                    "area": cluster["area"],
                    "restaurant_id": cluster["restaurant_id"],
                    "order_ids": [order["order_id"]],
                    "cluster_start_time": cluster["start_time"],
                    "rider_available_again_at": cluster["start_time"] + service_time,
                    "reused_rider": False,
                }
            )

        return clusters, assignments

    def _minute_value(self, order):
        from datetime import datetime

        ts = order.get("timestamp")
        if isinstance(ts, (int, float)):
            return int(ts)
        dt = datetime.fromisoformat(str(ts))
        return dt.hour * 60 + dt.minute
