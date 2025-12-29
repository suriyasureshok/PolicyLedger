"""
Explanation Metrics — Input to Explainability

Minimal input for explanation generation.
"""

from typing import NamedTuple, Optional, Dict, Any


class ExplanationMetrics(NamedTuple):
    """
    Input metrics for generating explanations.

    Only high-level outcomes, no internals.
    """
    environment_name: str
    policy_identifier: str
    verified_reward: float
    baseline_reward: Optional[float]  # None if no baseline available
    behavior_stats: Dict[str, Any]  # e.g., {"save_percentage": 0.6, "use_percentage": 0.8, "avg_battery": 0.75, "survived": True}

    def __repr__(self) -> str:
        return f"ExplanationMetrics(env={self.environment_name}, policy={self.policy_identifier}, reward={self.verified_reward}, baseline={self.baseline_reward}, stats={self.behavior_stats})"