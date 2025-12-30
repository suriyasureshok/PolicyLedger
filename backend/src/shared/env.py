"""
Backward compatibility shim for environment imports.

New code should import from src.environments directly.
This file maintained for existing imports.
"""

# Re-export for backward compatibility
from src.environments.energy_env import EnergySlotEnv
from src.environments.cyber_env import CyberDefenseEnv

__all__ = ["EnergySlotEnv", "CyberDefenseEnv"]
