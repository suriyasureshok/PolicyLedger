"""
runner.py

Orchestrates the complete agent training and policy submission workflow.

Detailed description:
- Provides the main entry point for agent training
- Coordinates environment setup, training, and policy extraction
- Produces verifiable policy claims for submission
- Saves policy artifacts for later reuse

Main Components:
- PolicyClaim: Data structure for policy submissions
- run_agent(): Main training orchestration function
- evaluate_policy(): Greedy policy evaluation
- quick_train(): Convenience training function

Dependencies:
- src.environments.cyber_env: CyberDefenseEnv for simulated cyber defense
- src.agent.trainer: Q-learning training functions
- src.agent.policy: Policy extraction and serialization
- src.agent.state: State discretization

Author: PolicyLedger Team
Created: 2025-12-28
Updated: 2025-12-30 (cyber defense refactor)

TODO: Google Cloud Integration
- Vertex AI: Use custom training jobs for distributed agent training
- Cloud Storage: Store policy artifacts in GCS buckets
- Firestore: Track training metrics and lineage
"""

from typing import NamedTuple
import json
from pathlib import Path
from src.environments.cyber_env import CyberDefenseEnv
from src.environments.base_env import BaseEnv
from src.shared.config import (
    DEFAULT_EPISODES,
    DEFAULT_TIME_HORIZON,
)
from src.agent.trainer import train
from src.agent.policy import extract_policy, serialize_policy, hash_policy, Policy
from src.agent.state import discretize_state


class PolicyClaim(NamedTuple):
    """
    Policy claim submitted by agent.

    This is what the agent produces - nothing more, nothing less.

    Attributes:
        agent_id: Unique identifier for this agent
        env_id: Environment configuration identifier (based on seed)
        policy_hash: SHA-256 hash of policy artifact
        policy_artifact: Serialized policy
        claimed_reward: Agent's claimed defense score (reward)
    """
    agent_id: str  # Unique identifier for this agent
    env_id: str  # Environment configuration identifier (based on seed)
    policy_hash: str  # SHA-256 hash of policy artifact
    policy_artifact: bytes  # Serialized policy
    claimed_reward: float  # Agent's claimed defense score

    def __repr__(self) -> str:
        return (
            f"PolicyClaim(\n"
            f"  agent_id='{self.agent_id}',\n"
            f"  env_id='{self.env_id}',\n"
            f"  policy_hash='{self.policy_hash[:16]}...',\n"
            f"  claimed_reward={self.claimed_reward:.3f}\n"
            f")"
        )


def evaluate_policy(env: BaseEnv, policy: Policy) -> float:
    """
    Evaluate a deterministic policy by running it greedily in the environment.

    This produces the reward that should be claimed (and verifiable).

    Args:
        env: Environment instance
        policy: Deterministic policy {state: action}

    Returns:
        Total reward from running policy greedily

    Rules:
        - No exploration (greedy only)
        - Single evaluation run
        - Uses exact same logic as verifier replay
    """
    # Reset environment
    state_dict = env.reset()

    # Accumulate reward
    total_reward = 0.0

    # Run episode
    while not env.done:
        # Discretize state
        state_tuple = discretize_state(state_dict)

        # Get action from policy (greedy)
        if state_tuple not in policy:
            raise ValueError(f"Policy incomplete: missing action for state {state_tuple}")

        action = policy[state_tuple]

        # Take action
        state_dict, reward, done = env.step(action)

        # Accumulate reward
        total_reward += reward

    return total_reward


def run_agent(
    agent_id: str,
    seed: int = 42,
    episodes: int = DEFAULT_EPISODES,
    time_horizon: int = DEFAULT_TIME_HORIZON,
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
        time_horizon: Simulation time horizon (number of decision steps)

    Returns:
        PolicyClaim containing all artifacts and claimed performance

    Rules:
        - Does NOT verify reward
        - Does NOT store to ledger
        - Does NOT rank policies
        - Does NOT see other agents
        - Just trains and claims
    """
    # Create simulated cyber defense environment with deterministic seed
    env = CyberDefenseEnv(
        time_horizon=time_horizon,
        seed=seed
    )

    # Generate environment ID (identifies configuration)
    env_id = f"cyber_defense_env_seed_{seed}_horizon_{time_horizon}"

    # Train policy with convergence detection
    q_table, avg_training_reward, training_stats = train(env, episodes)

    # Extract deterministic policy
    policy = extract_policy(q_table)

    # CRITICAL: Evaluate the final policy to get claimable reward
    # This must match what the verifier will compute during replay
    # The average training reward includes exploration and early learning,
    # but the verifier runs the greedy policy, so we must claim that reward.
    claimed_reward = evaluate_policy(env, policy)

    # Log training completion
    if training_stats['converged']:
        print(f"  ✓ Training converged after {training_stats['episodes_trained']} episodes")
    else:
        print(f"  ⚠ Training completed {training_stats['episodes_trained']} episodes without convergence")
    print(f"  📊 Q-table size: {training_stats['q_table_size']} state-action pairs")

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
        claimed_reward=claimed_reward  # Use evaluated reward, not training average
    )

    # Save policy artifact to disk for reuse
    _save_policy_artifact(policy_hash_str, policy, claimed_reward, agent_id)

    return claim


def _save_policy_artifact(policy_hash: str, policy: Policy, reward: float, agent_id: str):
    """
    Save policy artifact to disk for later reuse.

    Args:
        policy_hash: Hash of the policy
        policy: Policy dictionary
        reward: Claimed reward
        agent_id: Agent ID
    """
    policies_dir = Path("policies")
    policies_dir.mkdir(exist_ok=True)

    # Convert policy to serializable format
    serializable_policy = {str(k): v for k, v in policy.items()}

    artifact = {
        "policy": serializable_policy,
        "metadata": {
            "agent_id": agent_id,
            "claimed_reward": reward,
            "policy_hash": policy_hash
        }
    }

    artifact_path = policies_dir / f"{policy_hash}.json"
    with open(artifact_path, 'w') as f:
        json.dump(artifact, f, indent=2)


def quick_train(agent_id: str = "agent_001", seed: int = 42, episodes: int = 500) -> PolicyClaim:
    """
    Convenience function for quick testing.

    Uses default environment parameters with custom episodes.

    Args:
        agent_id: Unique identifier for this agent
        seed: Random seed for environment (for reproducibility)
        episodes: Number of training episodes

    Returns:
        PolicyClaim containing all artifacts and claimed performance
    """
    return run_agent(agent_id=agent_id, seed=seed, episodes=episodes)
