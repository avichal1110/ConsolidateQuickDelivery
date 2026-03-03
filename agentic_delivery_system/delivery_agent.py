"""DeliveryAgent: assigns riders to consolidated clusters with rider reuse."""

import heapq


class DeliveryAgent:
    """
    Time-aware rider assignment.

    Riders are reused once their previous delivery is complete.
    New riders are created only when no existing rider is available.
    """

    def _cluster_service_time(self, cluster):
        """Estimate rider busy duration for a cluster in minutes."""
        if not cluster.get("orders"):
            return 0

        durations = []
        for order in cluster["orders"]:
            eta = int(order.get("ETA_min", 0) or 0)
            travel = int(order.get("travel_time_min", 0) or 0)
            prep = int(order.get("prep_time_min", 0) or 0)
            durations.append(max(1, eta, travel + prep))

        return max(durations)

    def assign_riders(self, clusters):
        """
        Create rider assignments with rider reuse.

        Returns a list of assignment dicts:
        - rider_id
        - cluster_id
        - area
        - restaurant_id
        - order_ids
        - cluster_start_time
        - rider_available_again_at
        - reused_rider
        """
        if not clusters:
            return []

        sorted_clusters = sorted(
            clusters,
            key=lambda c: (c.get("start_time", 0), c.get("cluster_id", "")),
        )

        # Min-heap of (available_at_minute, rider_index)
        available_riders = []
        next_rider_index = 1
        assignments = []

        for cluster in sorted_clusters:
            start_time = int(cluster.get("start_time", 0))
            end_time = int(cluster.get("end_time", start_time))
            service_time = self._cluster_service_time(cluster)

            reused_rider = False
            if available_riders and available_riders[0][0] <= start_time:
                _, rider_index = heapq.heappop(available_riders)
                reused_rider = True
            else:
                rider_index = next_rider_index
                next_rider_index += 1

            rider_available_again_at = max(start_time, end_time) + service_time
            heapq.heappush(available_riders, (rider_available_again_at, rider_index))

            assignments.append(
                {
                    "rider_id": f"R{rider_index}",
                    "cluster_id": cluster["cluster_id"],
                    "area": cluster["area"],
                    "restaurant_id": cluster["restaurant_id"],
                    "order_ids": [order["order_id"] for order in cluster["orders"]],
                    "cluster_start_time": start_time,
                    "rider_available_again_at": rider_available_again_at,
                    "reused_rider": reused_rider,
                }
            )

        return assignments
