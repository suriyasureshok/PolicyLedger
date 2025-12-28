"""
Agent Runner - Orchestration Module

Glue everything together without owning logic.
This is the student submitting answer sheet + claimed marks.
"""

from typing import NamedTuple
from src.shared.env import EnergySlotEnv
from src.shared.config import (
    DEFAULT_EPISODES,
    DEFAULT_TIME_SLOTS,
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_ENERGY_COST
)
from src.agent.trainer import train
from src.agent.policy import extract_policy, serialize_policy, hash_policy


class PolicyClaim(NamedTuple):
    """
    Policy claim submitted by agent.
    
    This is what the agent produces - nothing more, nothing less.
    """
    agent_id: str  # Unique identifier for this agent
    env_id: str  # Environment configuration identifier (based on seed)
    policy_hash: str  # SHA-256 hash of policy artifact
    policy_artifact: bytes  # Serialized policy
    claimed_reward: float  # Agent's claimed average reward
    
    def __repr__(self) -> str:
        return (
            f"PolicyClaim(\n"
            f"  agent_id='{self.agent_id}',\n"
            f"  env_id='{self.env_id}',\n"
            f"  policy_hash='{self.policy_hash[:16]}...',\n"
            f"  claimed_reward={self.claimed_reward:.3f}\n"
            f")"
        )


def run_agent(
    agent_id: str,
    seed: int = 42,
    episodes: int = DEFAULT_EPISODES,
    time_slots: int = DEFAULT_TIME_SLOTS,
    battery_capacity: float = DEFAULT_BATTERY_CAPACITY,
    energy_cost: float = DEFAULT_ENERGY_COST
) -> PolicyClaim:
    """
    Run agent training and produce policy claim.
    
    This is the complete agent workflow:
    1. Create environment (with seed for reproducibility)
    2. Train policy using Q-learning
    3. Extract deterministic policy
    4. Serialize policy artifact
    5. Generate policy hash
    6. Create and return PolicyClaim
    
    Args:
        agent_id: Unique identifier for this agent
        seed: Random seed for environment (for reproducibility)
        episodes: Number of training episodes
        time_slots: Environment time horizon
        battery_capacity: Battery capacity
        energy_cost: Energy cost per USE action
    
    Returns:
        PolicyClaim containing all artifacts and claimed performance
    
    Rules:
        - Does NOT verify reward
        - Does NOT store to ledger
        - Does NOT rank policies
        - Does NOT see other agents
        - Just trains and claims
    """
    # Create environment with deterministic seed
    env = EnergySlotEnv(
        time_slots=time_slots,
        battery_capacity=battery_capacity,
        energy_cost=energy_cost,
        seed=seed
    )
    
    # Generate environment ID (identifies configuration)
    env_id = f"energy_slot_env_seed_{seed}_slots_{time_slots}"
    
    # Train policy
    q_table, avg_reward = train(env, episodes)
    
    # Extract deterministic policy
    policy = extract_policy(q_table)
    
    # Serialize policy
    policy_bytes = serialize_policy(policy)
    
    # Generate policy hash
    policy_hash_str = hash_policy(policy_bytes)
    
    # Create policy claim
    claim = PolicyClaim(
        agent_id=agent_id,
        env_id=env_id,
        policy_hash=policy_hash_str,
        policy_artifact=policy_bytes,
        claimed_reward=avg_reward
    )
    
    return claim


def quick_train(agent_id: str = "agent_001", seed: int = 42, episodes: int = 500) -> PolicyClaim:
    """
    Convenience function for quick testing.
    
    Uses default environment parameters with custom episodes.
    """
    return run_agent(agent_id=agent_id, seed=seed, episodes=episodes)
