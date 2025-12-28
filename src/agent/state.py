"""
state.py

State space discretization for Q-learning agent.

Detailed description:
- Converts continuous environment states into discrete state tuples
- Provides consistent state representation for Q-table indexing
- Pure function interface with no side effects

Main Components:
- discretize_state(): Core discretization function

Dependencies:
- src.shared.config: Bucket configuration constants

Author: PolicyLedger Team
Created: 2025-12-28
"""

from typing import Dict, Tuple
from src.shared.config import BATTERY_BUCKETS, TIME_SLOT_BUCKETS, DEFAULT_TIME_SLOTS


def discretize_state(env_state: Dict) -> Tuple[int, int, int]:
    """
    Convert continuous environment state into discrete state tuple.

    This is how the agent interprets the exam question. The discretization
    creates a finite state space suitable for Q-learning while preserving
    the essential decision-making information.

    Args:
        env_state: Raw state from environment containing:
            - time_slot: Current time slot (0 to time_slots-1)
            - battery_level: Continuous battery level (0.0 to 1.0)
            - demand: Binary demand (0 or 1)

    Returns:
        Tuple of (time_bucket, battery_bucket, demand) where:
        - time_bucket: Discretized time slot (0 to TIME_SLOT_BUCKETS-1)
        - battery_bucket: Discretized battery level (0 to BATTERY_BUCKETS-1)
        - demand: Binary demand (0 or 1)

        This tuple serves as the key in the Q-table.

    Rules:
        - Does NOT modify environment
        - Does NOT access Q-table
        - Does NOT use randomness
        - Pure function: same input → same output
        - Deterministic discretization ensures reproducible policies
    """
    time_slot = env_state["time_slot"]
    battery_level = env_state["battery_level"]
    demand = env_state["demand"]

    # Discretize time slot into buckets
    # Example: 24 slots → 6 buckets (each bucket covers 4 slots)
    slots_per_bucket = DEFAULT_TIME_SLOTS / TIME_SLOT_BUCKETS
    time_bucket = min(int(time_slot / slots_per_bucket), TIME_SLOT_BUCKETS - 1)

    # Discretize battery level into buckets
    # Battery ranges from 0.0 to 1.0
    # Clamp to valid range in case of numerical errors
    battery_clamped = max(0.0, min(1.0, battery_level))
    battery_bucket = min(int(battery_clamped * BATTERY_BUCKETS), BATTERY_BUCKETS - 1)

    # Demand is already discrete (0 or 1), keep as-is
    demand_discrete = int(demand)

    return (time_bucket, battery_bucket, demand_discrete)
