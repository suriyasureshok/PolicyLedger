"""
Agent Module - Phase 4: RL Agent (Edge Learning Node)

This module implements decentralized reinforcement learning.
Each agent learns independently and produces verifiable policy artifacts.
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
