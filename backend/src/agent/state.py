"""
state.py

State space discretization for Q-learning agent.

Detailed description:
- Converts environment states into discrete state tuples
- Provides consistent state representation for Q-table indexing
- Pure function interface with no side effects
- Supports both cyber defense and legacy energy environments

Main Components:
- discretize_state(): Core discretization function for cyber defense
- discretize_energy_state(): Legacy energy environment (backward compatibility)

Dependencies:
- src.shared.config: Bucket configuration constants

Author: PolicyLedger Team
Created: 2025-12-28
Updated: 2025-12-30 (cyber defense refactor)
"""

from typing import Dict, Tuple
from src.shared.config import (
    BATTERY_BUCKETS, 
    TIME_SLOT_BUCKETS, 
    DEFAULT_TIME_SLOTS
)


def discretize_state(env_state: Dict) -> Tuple:
    """
    Convert environment state into discrete state tuple.
    
    Automatically detects environment type and applies appropriate discretization.
    
    Args:
        env_state: Raw state from environment
    
    Returns:
        Discrete state tuple suitable for Q-table indexing
    
    Rules:
        - Does NOT modify environment
        - Does NOT access Q-table
        - Does NOT use randomness
        - Pure function: same input → same output
        - Deterministic discretization ensures reproducible policies
    """
    # Detect environment type by state keys
    if "attack_severity" in env_state:
        # Cyber defense environment
        return discretize_cyber_state(env_state)
    elif "time_slot" in env_state and "battery_level" in env_state:
        # Legacy energy environment
        return discretize_energy_state(env_state)
    else:
        raise ValueError(f"Unknown environment state format: {env_state.keys()}")


def discretize_cyber_state(env_state: Dict) -> Tuple[int, int, int, int, int]:
    """
    Convert cyber defense environment state into discrete state tuple.
    
    State space for cyber defense:
    - attack_severity: 0 (LOW), 1 (MEDIUM), 2 (HIGH)
    - attack_type: 0 (SCAN), 1 (BRUTE_FORCE), 2 (DOS)
    - system_health: 0 (HEALTHY), 1 (DEGRADED), 2 (CRITICAL)
    - alert_confidence: 0 (LOW), 1 (HIGH)
    - time_under_attack: 0 (SHORT), 1 (LONG)
    
    Args:
        env_state: Raw state from CyberDefenseEnv containing:
            - attack_severity: Attack severity level (0-2)
            - attack_type: Type of attack (0-2)
            - system_health: System health status (0-2)
            - alert_confidence: Alert confidence (0-1)
            - time_under_attack: Attack duration indicator (0-1)
    
    Returns:
        Tuple of (attack_severity, attack_type, system_health, alert_confidence, time_under_attack)
        All values are already discrete, so we just extract and validate them.
    """
    # Extract state components (already discrete from environment)
    attack_severity = int(env_state["attack_severity"])
    attack_type = int(env_state["attack_type"])
    system_health = int(env_state["system_health"])
    alert_confidence = int(env_state["alert_confidence"])
    time_under_attack = int(env_state["time_under_attack"])
    
    # Validate ranges (safety check)
    assert 0 <= attack_severity <= 2, f"Invalid attack_severity: {attack_severity}"
    assert 0 <= attack_type <= 2, f"Invalid attack_type: {attack_type}"
    assert 0 <= system_health <= 2, f"Invalid system_health: {system_health}"
    assert 0 <= alert_confidence <= 1, f"Invalid alert_confidence: {alert_confidence}"
    assert 0 <= time_under_attack <= 1, f"Invalid time_under_attack: {time_under_attack}"
    
    return (attack_severity, attack_type, system_health, alert_confidence, time_under_attack)


def discretize_energy_state(env_state: Dict) -> Tuple[int, int, int]:
    """
    Convert energy environment state into discrete state tuple.
    
    LEGACY: This function supports the original energy scheduling environment.
    New development should use cyber defense environment.
    
    Args:
        env_state: Raw state from EnergySlotEnv containing:
            - time_slot: Current time slot (0 to time_slots-1)
            - battery_level: Continuous battery level (0.0 to 1.0)
            - demand: Binary demand (0 or 1)

    Returns:
        Tuple of (time_bucket, battery_bucket, demand) where:
        - time_bucket: Discretized time slot (0 to TIME_SLOT_BUCKETS-1)
        - battery_bucket: Discretized battery level (0 to BATTERY_BUCKETS-1)
        - demand: Binary demand (0 or 1)
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
