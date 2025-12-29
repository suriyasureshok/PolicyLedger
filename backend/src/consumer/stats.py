"""
Execution Stats — Collected during policy execution
"""

from typing import NamedTuple

class ExecutionStats(NamedTuple):
    """
    Statistics collected during policy execution.
    """
    avg_reward: float
    save_percentage: float
    use_percentage: float
    avg_battery: float
    survival_rate: float  # % of episodes survived to horizon