"""DeliveryAgent: assigns riders to consolidated clusters with rider reuse."""

import heapq


class DeliveryAgent:
    """
    Time-aware, capacity-aware rider assignment.

    Riders are reused once their previous delivery is complete. New riders
    are created only when no existing rider is available. A cluster larger
    than a single rider's vehicle capacity is split into multiple
    capacity-respecting batches rather than assigned to one rider regardless
    of size.
    """

    def _cluster_service_time(self, orders):
        """Estimate rider busy duration for a set of orders in minutes."""
        if not orders:
            return 0

        durations = []
        for order in orders:
            eta = int(order.get("ETA_min", 0) or 0)
            travel = int(order.get("travel_time_min", 0) or 0)
            prep = int(order.get("prep_time_min", 0) or 0)
            durations.append(max(1, eta, travel + prep))

        return max(durations)

    def _capacity_for_cluster(self, cluster, default_capacity=3):
        """
        Determine the safe vehicle capacity for a cluster.

        Uses the smallest vehicle_capacity reported across the cluster's
        orders, since the assigned rider must be able to carry every order
        in the batch. Falls back to default_capacity if the field is absent
        (keeps backward compatibility with older/synthetic datasets).
        """
        capacities = [
            int(order["vehicle_capacity"])
            for order in cluster.get("orders", [])
            if order.get("vehicle_capacity") not in (None, "")
        ]
        if not capacities:
            return default_capacity
        return max(1, min(capacities))

    def _split_by_capacity(self, cluster):
        """Split a cluster's orders into capacity-respecting batches."""
        capacity = self._capacity_for_cluster(cluster)
        orders = cluster["orders"]
        batches = [orders[i:i + capacity] for i in range(0, len(orders), capacity)]
        return batches, capacity

    def assign_riders(self, clusters):
        """
        Create rider assignments with rider reuse and capacity splitting.

        Returns a list of assignment dicts:
        - rider_id
        - cluster_id
        - area
        - restaurant_id
        - order_ids
        - cluster_start_time
        - rider_available_again_at
        - reused_rider
        - vehicle_capacity_used
        - split_batch (True if this cluster required more than one rider
          due to vehicle capacity)
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

            batches, capacity = self._split_by_capacity(cluster)
            split_batch = len(batches) > 1

            for batch in batches:
                service_time = self._cluster_service_time(batch)

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
                        "order_ids": [order["order_id"] for order in batch],
                        "cluster_start_time": start_time,
                        "rider_available_again_at": rider_available_again_at,
                        "reused_rider": reused_rider,
                        "vehicle_capacity_used": capacity,
                        "split_batch": split_batch,
                    }
                )

        return assignments

