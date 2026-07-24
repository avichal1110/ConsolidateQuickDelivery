"""
MLDemandAgent: forecasts order volume for the *next* 5-minute window using
a trained regression model, instead of just counting orders already in a
trailing window (what the rule-based DemandAgent does).

Why this is different from the rule-based agent:
- DemandAgent looks backward: "how many orders arrived in the last 10 min?"
- MLDemandAgent looks forward: "how many orders do I expect in the next
  5 min, given current conditions (traffic, surge, pending orders, time
  of day)?" This gives the DispatchAgent earlier warning of a demand spike,
  rather than reacting only after it's already happened.

Drop-in compatible with DemandAgent: assess_demand(orders) returns the
same (level, count, start_time, end_time) tuple, so it can be swapped into
main.py or evaluate.py without changing anything downstream.
"""

from sklearn.ensemble import RandomForestRegressor

from demand_features import build_window_table, FEATURE_COLUMNS, WINDOW_MINUTES


class MLDemandAgent:
    def __init__(self, low_threshold=3, high_threshold=7, window_minutes=WINDOW_MINUTES,
                 n_estimators=200, random_state=42):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.window_minutes = window_minutes
        self.model = RandomForestRegressor(
            n_estimators=n_estimators, max_depth=6, random_state=random_state
        )
        self._fitted = False

    def fit(self, historical_orders):
        """Train the forecasting model on historical order data."""
        table = build_window_table(historical_orders, self.window_minutes)
        X = table[FEATURE_COLUMNS]
        y = table["target_next_count"]
        self.model.fit(X, y)
        self._fitted = True
        self._last_table = table
        return self

    def _classify(self, predicted_count):
        if predicted_count <= self.low_threshold:
            return "LOW"
        if predicted_count <= self.high_threshold:
            return "MEDIUM"
        return "HIGH"

    def assess_demand(self, orders):
        """
        Predict demand for the window immediately following the most
        recent order in `orders`. Falls back to a simple persistence
        estimate if the model hasn't been trained yet.
        """
        if not orders:
            return "LOW", 0, 0, 0

        table = build_window_table(orders, self.window_minutes)
        if table.empty:
            return "LOW", 0, 0, 0

        latest = table.iloc[[-1]]
        start_t = int(latest["window"].iloc[0]) * self.window_minutes
        end_t = start_t + self.window_minutes

        if not self._fitted:
            # Fallback: persistence (assume next window looks like current one)
            predicted = float(latest["order_count"].iloc[0])
        else:
            predicted = float(self.model.predict(latest[FEATURE_COLUMNS])[0])

        level = self._classify(predicted)
        return level, round(predicted, 1), start_t, end_t
