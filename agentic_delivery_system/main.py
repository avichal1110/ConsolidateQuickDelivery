"""
Main script to run the end-to-end agentic delivery simulation.
"""

from data import get_orders
from demand_agent import DemandAgent
from consolidation_agent import ConsolidationAgent
from dispatch_agent import DispatchAgent
from delivery_agent import DeliveryAgent


def print_clusters(clusters):
    """Pretty-print consolidated clusters."""
    if not clusters:
        print("No clusters created.")
        return

    for cluster in clusters:
        order_ids = [order["order_id"] for order in cluster["orders"]]
        print(
            f"  {cluster['cluster_id']}: "
            f"Area={cluster['area']}, RestaurantID={cluster['restaurant_id']}, "
            f"TimeWindow={cluster['start_time']}-{cluster['end_time']} min, "
            f"Orders={order_ids}"
        )


def print_assignments(assignments):
    """Pretty-print rider assignments."""
    if not assignments:
        print("No assignments generated.")
        return

    for item in assignments:
        print(
            f"  Rider {item['rider_id']} -> {item['cluster_id']} "
            f"({item['area']} | {item['restaurant_id']}) | Orders={item['order_ids']}"
        )


def main():
    # 1. Load orders from CSV dataset.
    orders = get_orders()

    # 2. Agent initialization.
    demand_agent = DemandAgent(window_minutes=10, low_threshold=3, high_threshold=7)
    consolidation_agent = ConsolidationAgent(consolidation_window=5)
    dispatch_agent = DispatchAgent(high_demand_wait_minutes=5)
    delivery_agent = DeliveryAgent()

    # 3. Demand estimation.
    demand_level, recent_count, start_t, end_t = demand_agent.assess_demand(orders)

    # 4. Order consolidation.
    clusters = consolidation_agent.consolidate(orders)

    # 5. Dispatch decision.
    dispatch = dispatch_agent.dispatch_decision(demand_level, clusters)

    # 6. Delivery assignment.
    assignments = delivery_agent.assign_riders(clusters)

    # 7. Output.
    print("\n=== AGENTIC DELIVERY SYSTEM OUTPUT ===")
    print(f"Total Orders Loaded: {len(orders)}")
    print(f"Demand Level: {demand_level}")
    print(f"Recent Orders in Window ({start_t} to {end_t} min): {recent_count}")

    print("\nConsolidated Orders:")
    print_clusters(clusters)

    print("\nDispatch Decision:")
    print(
        f"  Action={dispatch['action']}, "
        f"WaitMinutes={dispatch['wait_minutes']}, "
        f"Reason={dispatch['reason']}"
    )

    print("\nDelivery Assignment:")
    print_assignments(assignments)


if __name__ == "__main__":
    main()
