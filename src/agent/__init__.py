"""
agent

Purpose:
- Implements decentralized reinforcement learning agents
- Provides complete RL pipeline from training to policy submission
- Enables edge learning with verifiable policy artifacts

Public Exports:
- run_agent: Main training orchestration function
- quick_train: Convenience training function
- PolicyClaim: Data structure for policy submissions
- discretize_state: State space discretization
- Training utilities (initialize_q_table, select_action, etc.)
- Policy utilities (extract_policy, serialize_policy, etc.)

Usage:
    from src.agent import run_agent, PolicyClaim

    # Train an agent
    claim = run_agent(agent_id="agent_001", seed=42, episodes=500)
"""

from src.agent.runner import run_agent, quick_train, PolicyClaim
from src.agent.state import discretize_state
from src.agent.trainer import (
    initialize_q_table,
    select_action,
    update_q_value,
    train_episode,
    train,
    ACTION_SAVE,
    ACTION_USE,
)
from src.agent.policy import (
    extract_policy,
    serialize_policy,
    deserialize_policy,
    hash_policy,
)

__all__ = [
    # Main entry point
    "run_agent",
    "quick_train",
    "PolicyClaim",
    # State handling
    "discretize_state",
    # Training functions
    "initialize_q_table",
    "select_action",
    "update_q_value",
    "train_episode",
    "train",
    # Actions
    "ACTION_SAVE",
    "ACTION_USE",
    # Policy handling
    "extract_policy",
    "serialize_policy",
    "deserialize_policy",
    "hash_policy",
]
