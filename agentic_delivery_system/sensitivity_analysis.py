"""
Sensitivity analysis: sweeps the consolidation window parameter to show
the tradeoff between fleet size (riders needed) and batching aggressiveness,
justifying the choice of a 5-minute default rather than asserting it.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data import get_orders
from consolidation_agent import ConsolidationAgent
from delivery_agent import DeliveryAgent
from evaluate import evaluate_assignments


def main():
    orders = get_orders()
    delivery_agent = DeliveryAgent()

    windows = [1, 2, 3, 5, 7, 10, 15, 20]
    riders_used = []
    avg_cluster_sizes = []

    print(f"{'Window (min)':<15}{'Riders Used':<15}{'Avg Cluster Size':<18}{'% Batched'}")
    print("-" * 60)

    for w in windows:
        agent = ConsolidationAgent(consolidation_window=w)
        clusters = agent.consolidate(orders)
        assignments = delivery_agent.assign_riders(clusters)
        metrics = evaluate_assignments(clusters, assignments)

        riders_used.append(metrics["riders_used"])
        avg_cluster_sizes.append(metrics["avg_cluster_size"])
        print(f"{w:<15}{metrics['riders_used']:<15}{metrics['avg_cluster_size']:<18}"
              f"{metrics['pct_orders_batched']}")

    # Plot: riders needed vs. consolidation window
    fig, ax1 = plt.subplots(figsize=(7, 4.5))

    color1 = "#2563eb"
    ax1.set_xlabel("Consolidation window (minutes)")
    ax1.set_ylabel("Riders needed", color=color1)
    ax1.plot(windows, riders_used, marker="o", color=color1, linewidth=2)
    ax1.tick_params(axis="y", labelcolor=color1)

    ax2 = ax1.twinx()
    color2 = "#dc2626"
    ax2.set_ylabel("Avg orders per cluster", color=color2)
    ax2.plot(windows, avg_cluster_sizes, marker="s", color=color2, linewidth=2, linestyle="--")
    ax2.tick_params(axis="y", labelcolor=color2)

    plt.title("Effect of Consolidation Window on Fleet Size and Batching")
    fig.tight_layout()
    plt.savefig("sensitivity_chart.png", dpi=150)
    print("\nChart saved -> sensitivity_chart.png")


if __name__ == "__main__":
    main()
