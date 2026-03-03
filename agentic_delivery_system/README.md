# Agentic Delivery System 

## Problem Statement
This project simulates how a delivery platform (like Swiggy, fast-food delivery, or e-commerce last-mile) can make **coordinated operational decisions** using multiple software agents.

The focus is on **agent-based decision making**, not prediction accuracy.

## Why Agentic AI Here?
A single script can work, but splitting logic into agents makes decisions easier to explain and extend.

This system has four simple agents:
- `DemandAgent`: checks recent order volume and labels demand as `LOW`, `MEDIUM`, or `HIGH`.
- `ConsolidationAgent`: clubs orders using clear rules (same area, same restaurant, close in time).
- `DispatchAgent`: decides whether to dispatch now or wait based on demand.
- `DeliveryAgent`: assigns one rider per order cluster.

This mirrors real operations where specialized components collaborate.


The data in `data.py` is fully dummy and Swiggy-like in structure.

## Project Structure

```text
agentic_delivery_system/
+-- data.py
+-- demand_agent.py
+-- consolidation_agent.py
+-- dispatch_agent.py
+-- delivery_agent.py
+-- main.py
+-- README.md
```

## How to Run

1. Open terminal in `agentic_delivery_system`.
2. Run:

```bash
python main.py
```

## What `main.py` Prints
- Demand level
- Consolidated orders (clusters)
- Dispatch decision
- Delivery assignments

## Core Rules Implemented
1. **Demand Rule**: based on count of orders in recent time window.
2. **Consolidation Rule**: same area + same restaurant + within 5 minutes.
3. **Dispatch Rule**:
   - `HIGH` demand -> wait 5 minutes
   - otherwise -> dispatch immediately
4. **Delivery Rule**: one rider per cluster.

## How This Can Scale to Real Platforms
This foundation can be extended in multiple directions:
- Replace synthetic data with database/stream input.
- Upgrade demand rule to ML forecasting.
- Improve clustering with route/time-distance constraints.
- Add rider availability, traffic, and SLA constraints.
- Introduce LLM-based explanation layer for operations teams.


