"""
Evaluation harness: runs the agentic pipeline and the naive baseline on
the same order set and reports the metrics that matter for a delivery
operations comparison.

Metrics reported:
- Total riders required
- Average orders served per rider (utilization)
- Average cluster size (consolidation effectiveness)
- % of orders that were batched with at least one other order
- Total rider-minutes of work (proxy for fleet cost)
- Average dispatch wait added per order
"""

import statistics
from data import get_orders
from demand_agent import DemandAgent
from consolidation_agent import ConsolidationAgent
from dispatch_agent import DispatchAgent
from delivery_agent import DeliveryAgent
from baseline_system import BaselineSystem


def evaluate_assignments(clusters, assignments, extra_wait_minutes=0):
    n_orders = sum(len(c["orders"]) for c in clusters)
    n_riders = len(set(a["rider_id"] for a in assignments))
    cluster_sizes = [len(c["orders"]) for c in clusters]
    batched_orders = sum(size for size in cluster_sizes if size > 1)

    rider_minutes = sum(
        (a["rider_available_again_at"] - a["cluster_start_time"]) for a in assignments
    )

    return {
        "orders": n_orders,
        "riders_used": n_riders,
        "orders_per_rider": round(n_orders / n_riders, 2) if n_riders else 0,
        "avg_cluster_size": round(statistics.mean(cluster_sizes), 2) if cluster_sizes else 0,
        "pct_orders_batched": round(100 * batched_orders / n_orders, 1) if n_orders else 0,
        "total_rider_minutes": rider_minutes,
        "avg_dispatch_wait_min": extra_wait_minutes,
    }


def main():
    orders = get_orders()

    # --- Agentic system ---
    demand_agent = DemandAgent(window_minutes=10, low_threshold=3, high_threshold=7)
    consolidation_agent = ConsolidationAgent(consolidation_window=5)
    dispatch_agent = DispatchAgent(high_demand_wait_minutes=5)
    delivery_agent = DeliveryAgent()

    demand_level, recent_count, start_t, end_t = demand_agent.assess_demand(orders)
    clusters = consolidation_agent.consolidate(orders)
    dispatch = dispatch_agent.dispatch_decision(demand_level, clusters)
    assignments = delivery_agent.assign_riders(clusters)

    agentic_wait = dispatch["wait_minutes"] if dispatch["action"] == "WAIT" else 0
    agentic_metrics = evaluate_assignments(clusters, assignments, agentic_wait)

    # --- Baseline (naive) system ---
    baseline = BaselineSystem()
    base_clusters, base_assignments = baseline.run(orders)
    baseline_metrics = evaluate_assignments(base_clusters, base_assignments, 0)

    # --- Report ---
    print("=" * 70)
    print("EVALUATION: Agentic System vs. Naive Baseline")
    print("=" * 70)
    print(f"Total orders evaluated: {len(orders)}")
    print(f"Demand level detected (agentic): {demand_level} "
          f"({recent_count} orders in most recent {end_t - start_t}-min window)")
    print()

    header = f"{'Metric':<30}{'Agentic':<18}{'Baseline':<18}{'Delta'}"
    print(header)
    print("-" * len(header))

    def pct_change(new, old):
        if old == 0:
            return "n/a"
        change = 100 * (new - old) / old
        sign = "+" if change >= 0 else ""
        return f"{sign}{change:.1f}%"

    rows = [
        ("Riders used", "riders_used"),
        ("Orders per rider", "orders_per_rider"),
        ("Avg cluster size", "avg_cluster_size"),
        ("% orders batched", "pct_orders_batched"),
        ("Total rider-minutes", "total_rider_minutes"),
        ("Avg dispatch wait (min)", "avg_dispatch_wait_min"),
    ]

    for label, key in rows:
        a_val = agentic_metrics[key]
        b_val = baseline_metrics[key]
        delta = pct_change(a_val, b_val)
        print(f"{label:<30}{str(a_val):<18}{str(b_val):<18}{delta}")

    print()
    riders_saved = baseline_metrics["riders_used"] - agentic_metrics["riders_used"]
    pct_saved = (
        round(100 * riders_saved / baseline_metrics["riders_used"], 1)
        if baseline_metrics["riders_used"] else 0
    )
    print(f"Fleet reduction: {riders_saved} fewer riders needed "
          f"({pct_saved}% reduction vs. naive baseline)")
    print(f"Tradeoff: agentic system adds up to {agentic_metrics['avg_dispatch_wait_min']} "
          f"min dispatch delay during HIGH demand to achieve this.")


if __name__ == "__main__":
    main()
