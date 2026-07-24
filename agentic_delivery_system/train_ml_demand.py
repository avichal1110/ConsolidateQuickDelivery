"""
Trains MLDemandAgent on the first part of the day's orders and evaluates
its forecasting accuracy on the held-out remainder, comparing against a
naive "persistence" baseline (predict next window = current window count).

This answers the question a professor is likely to ask: "does the ML
model actually forecast demand better than just assuming things stay the
same as right now?"
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from data import get_orders
from demand_features import build_window_table, FEATURE_COLUMNS
from ml_demand_agent import MLDemandAgent


def mae(y_true, y_pred):
    return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.array(y_true) - np.array(y_pred)) ** 2)))


def main():
    orders = get_orders()
    table = build_window_table(orders)

    split_idx = int(len(table) * 0.7)
    train_table = table.iloc[:split_idx]
    test_table = table.iloc[split_idx:]

    print(f"Total 5-min windows: {len(table)} | Train: {len(train_table)} | Test: {len(test_table)}")

    # --- Train ML model on the training slice only ---
    agent = MLDemandAgent()
    X_train = train_table[FEATURE_COLUMNS]
    y_train = train_table["target_next_count"]
    agent.model.fit(X_train, y_train)
    agent._fitted = True

    # --- Predict on held-out test slice ---
    X_test = test_table[FEATURE_COLUMNS]
    y_test = test_table["target_next_count"].values
    ml_predictions = agent.model.predict(X_test)

    # --- Persistence baseline: predict next = current window's count ---
    persistence_predictions = test_table["order_count"].values

    print()
    print(f"{'Model':<25}{'MAE':<12}{'RMSE'}")
    print("-" * 47)
    print(f"{'Persistence baseline':<25}{mae(y_test, persistence_predictions):<12.2f}"
          f"{rmse(y_test, persistence_predictions):.2f}")
    print(f"{'ML (Random Forest)':<25}{mae(y_test, ml_predictions):<12.2f}"
          f"{rmse(y_test, ml_predictions):.2f}")

    improvement = 100 * (mae(y_test, persistence_predictions) - mae(y_test, ml_predictions)) \
        / mae(y_test, persistence_predictions)
    print(f"\nML reduces forecast error (MAE) by {improvement:.1f}% vs. persistence baseline.")

    # --- Chart: actual vs ML-predicted vs persistence, over test windows ---
    plt.figure(figsize=(8, 4.5))
    window_starts = test_table["window"].values * 5
    plt.plot(window_starts, y_test, label="Actual", color="#111827", linewidth=2)
    plt.plot(window_starts, ml_predictions, label="ML forecast", color="#2563eb",
              linewidth=2, linestyle="--")
    plt.plot(window_starts, persistence_predictions, label="Persistence baseline",
              color="#dc2626", linewidth=1.5, linestyle=":")
    plt.xlabel("Minutes from midnight")
    plt.ylabel("Orders in next 5-min window")
    plt.title("ML Demand Forecast vs. Actual (held-out test period)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("ml_demand_forecast_chart.png", dpi=150)
    print("\nChart saved -> ml_demand_forecast_chart.png")

    # --- Feature importance, for interpretability ---
    importances = sorted(
        zip(FEATURE_COLUMNS, agent.model.feature_importances_),
        key=lambda x: -x[1],
    )
    print("\nTop features driving the forecast:")
    for name, imp in importances[:5]:
        print(f"  {name:<32}{imp:.3f}")


if __name__ == "__main__":
    main()
