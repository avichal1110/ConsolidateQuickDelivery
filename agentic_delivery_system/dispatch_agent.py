"""
DispatchAgent: decides whether to dispatch now or wait.
"""


class DispatchAgent:
    """
    Rule-based dispatch decision maker.

    Rule:
    - If demand is HIGH -> wait 5 minutes before dispatch
    - Else -> dispatch immediately
    """

    def __init__(self, high_demand_wait_minutes=5):
        self.high_demand_wait_minutes = high_demand_wait_minutes

    def dispatch_decision(self, demand_level, clusters):
        """
        Decide dispatch strategy based on demand.

        Returns a dict with:
        - action: WAIT or DISPATCH_NOW
        - wait_minutes
        - reason
        - cluster_count
        """
        if demand_level == "HIGH":
            return {
                "action": "WAIT",
                "wait_minutes": self.high_demand_wait_minutes,
                "reason": "High demand detected; waiting briefly can increase consolidation.",
                "cluster_count": len(clusters),
            }

        return {
            "action": "DISPATCH_NOW",
            "wait_minutes": 0,
            "reason": "Demand is not high; immediate dispatch reduces delivery delay.",
            "cluster_count": len(clusters),
        }
