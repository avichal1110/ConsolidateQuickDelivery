"""
Basic unit tests for the agentic delivery system.

Run with: python -m unittest test_agents.py -v
(or: pytest test_agents.py -v)
"""

import unittest
from demand_agent import DemandAgent
from consolidation_agent import ConsolidationAgent
from dispatch_agent import DispatchAgent
from delivery_agent import DeliveryAgent


def make_order(order_id, minute, area="Andheri East", restaurant_id="REST_A",
                eta=20, travel=10, prep=10, vehicle_capacity=None):
    order = {
        "order_id": order_id,
        "timestamp": f"2026-01-01T{minute // 60:02d}:{minute % 60:02d}:00",
        "area": area,
        "restaurant_id": restaurant_id,
        "ETA_min": eta,
        "travel_time_min": travel,
        "prep_time_min": prep,
    }
    if vehicle_capacity is not None:
        order["vehicle_capacity"] = vehicle_capacity
    return order


class TestDemandAgent(unittest.TestCase):
    def setUp(self):
        self.agent = DemandAgent(window_minutes=10, low_threshold=3, high_threshold=7)

    def test_low_demand(self):
        orders = [make_order(f"O{i}", 100 + i) for i in range(2)]
        level, count, _, _ = self.agent.assess_demand(orders)
        self.assertEqual(level, "LOW")
        self.assertEqual(count, 2)

    def test_high_demand(self):
        orders = [make_order(f"O{i}", 100 + i) for i in range(9)]
        level, count, _, _ = self.agent.assess_demand(orders)
        self.assertEqual(level, "HIGH")

    def test_empty_orders(self):
        level, count, start, end = self.agent.assess_demand([])
        self.assertEqual(count, 0)


class TestConsolidationAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ConsolidationAgent(consolidation_window=5)

    def test_same_area_restaurant_within_window_clusters_together(self):
        orders = [
            make_order("O1", 100),
            make_order("O2", 102),
        ]
        clusters = self.agent.consolidate(orders)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(len(clusters[0]["orders"]), 2)

    def test_different_restaurant_does_not_cluster(self):
        orders = [
            make_order("O1", 100, restaurant_id="REST_A"),
            make_order("O2", 101, restaurant_id="REST_B"),
        ]
        clusters = self.agent.consolidate(orders)
        self.assertEqual(len(clusters), 2)

    def test_outside_window_does_not_cluster(self):
        orders = [
            make_order("O1", 100),
            make_order("O2", 110),  # 10 min later, window is 5
        ]
        clusters = self.agent.consolidate(orders)
        self.assertEqual(len(clusters), 2)


class TestDispatchAgent(unittest.TestCase):
    def setUp(self):
        self.agent = DispatchAgent(high_demand_wait_minutes=5)

    def test_high_demand_waits(self):
        decision = self.agent.dispatch_decision("HIGH", [])
        self.assertEqual(decision["action"], "WAIT")
        self.assertEqual(decision["wait_minutes"], 5)

    def test_low_demand_dispatches_immediately(self):
        decision = self.agent.dispatch_decision("LOW", [])
        self.assertEqual(decision["action"], "DISPATCH_NOW")


class TestDeliveryAgent(unittest.TestCase):
    def setUp(self):
        self.agent = DeliveryAgent()

    def test_single_cluster_gets_one_rider(self):
        cluster = {
            "cluster_id": "C1", "area": "Andheri East", "restaurant_id": "REST_A",
            "start_time": 100, "end_time": 100,
            "orders": [make_order("O1", 100)],
        }
        assignments = self.agent.assign_riders([cluster])
        self.assertEqual(len(assignments), 1)

    def test_rider_is_reused_when_free_in_time(self):
        early = {
            "cluster_id": "C1", "area": "A", "restaurant_id": "R1",
            "start_time": 0, "end_time": 0,
            "orders": [make_order("O1", 0, eta=5, travel=2, prep=2)],
        }
        later = {
            "cluster_id": "C2", "area": "A", "restaurant_id": "R1",
            "start_time": 100, "end_time": 100,
            "orders": [make_order("O2", 100, eta=5, travel=2, prep=2)],
        }
        assignments = self.agent.assign_riders([early, later])
        self.assertTrue(assignments[1]["reused_rider"])
        self.assertEqual(assignments[0]["rider_id"], assignments[1]["rider_id"])

    def test_cluster_exceeding_vehicle_capacity_splits_into_two_riders(self):
        cluster = {
            "cluster_id": "C1", "area": "A", "restaurant_id": "R1",
            "start_time": 0, "end_time": 0,
            "orders": [make_order(f"O{i}", 0, vehicle_capacity=2) for i in range(4)],
        }
        assignments = self.agent.assign_riders([cluster])
        self.assertEqual(len(assignments), 2)
        self.assertTrue(all(a["split_batch"] for a in assignments))
        total_orders = sum(len(a["order_ids"]) for a in assignments)
        self.assertEqual(total_orders, 4)


if __name__ == "__main__":
    unittest.main()
