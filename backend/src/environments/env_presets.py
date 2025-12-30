"""
Environment Configuration Presets

Define different environment configurations to segregate agents by training difficulty
and scenario type. This enables fair comparisons within environment categories.
"""

from typing import Dict
from dataclasses import dataclass, asdict


@dataclass
class EnvironmentConfig:
    """Environment configuration for agent training"""
    env_type: str  # Unique identifier (e.g., "standard", "high_attack", "long_duration")
    display_name: str  # Human-readable name
    time_horizon: int  # Episode length
    description: str  # Description of environment characteristics
    seed_base: int  # Base seed for this environment type
    
    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# ENVIRONMENT PRESETS
# =============================================================================

ENV_PRESETS = {
    "standard": EnvironmentConfig(
        env_type="standard",
        display_name="Standard Environment",
        time_horizon=24,
        description="Balanced attack patterns, 24-step episodes",
        seed_base=42
    ),
    
    "short_burst": EnvironmentConfig(
        env_type="short_burst",
        display_name="Short Burst",
        time_horizon=12,
        description="Quick response scenarios, 12-step episodes",
        seed_base=100
    ),
    
    "extended": EnvironmentConfig(
        env_type="extended",
        display_name="Extended Duration",
        time_horizon=48,
        description="Long-term defense scenarios, 48-step episodes",
        seed_base=200
    ),
    
    "high_pressure": EnvironmentConfig(
        env_type="high_pressure",
        display_name="High Pressure",
        time_horizon=24,
        description="Frequent high-severity attacks, testing aggressive defense",
        seed_base=300
    ),
    
    "sparse_attacks": EnvironmentConfig(
        env_type="sparse_attacks",
        display_name="Sparse Attacks",
        time_horizon=24,
        description="Rare but critical attacks, testing vigilance",
        seed_base=400
    ),
}


def get_env_config(env_type: str = "standard") -> EnvironmentConfig:
    """Get environment configuration by type"""
    if env_type not in ENV_PRESETS:
        print(f"Warning: Unknown env_type '{env_type}', using 'standard'")
        return ENV_PRESETS["standard"]
    return ENV_PRESETS[env_type]


def list_env_types() -> list:
    """List all available environment types"""
    return [
        {
            "env_type": config.env_type,
            "display_name": config.display_name,
            "description": config.description,
            "time_horizon": config.time_horizon
        }
        for config in ENV_PRESETS.values()
    ]
