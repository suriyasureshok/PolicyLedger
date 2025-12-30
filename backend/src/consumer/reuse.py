"""
reuse.py

Policy reuse module for executing pre-trained policies instantly.

Detailed description:
- What problem this module solves: Enables instant reuse of verified, pre-trained policies without retraining, allowing consumers to leverage learned intelligence immediately
- What it does NOT do: Does not perform training, verification, or policy modification; focuses solely on execution and comparison
- Any assumptions or constraints: Assumes policies are pre-verified and stored in JSON format; requires deterministic execution for reproducibility

Main Components:
- BaselinePolicy: Enum defining simple baseline strategies for performance comparison
- PolicyConsumer: Class for loading and executing pre-trained policies deterministically
- compare_with_baseline(): Compares policy performance against baseline strategies
- reuse_best_policy(): Convenience function to load and execute the best policy from marketplace

Dependencies:
- json: For policy artifact serialization
- pathlib: For file system operations
- typing: For type hints
- enum: For BaselinePolicy enumeration
- random: For baseline policy randomization
- src.environments.cyber_env: CyberDefenseEnv for simulated cyber defense
- src.agent.state: discretize_state for state processing
- src.marketplace.ranking: BestPolicyReference for policy selection

Author: PolicyLedger Team
Created: 2025-12-28
Updated: 2025-12-30 (cyber defense refactor)

TODO: Google Cloud Integration
- Cloud Storage: Fetch policies from GCS instead of local filesystem
- Cloud Functions: Trigger policy execution on marketplace updates
"""

import json
from pathlib import Path
from typing import Dict, Tuple, Optional
from enum import Enum
import random

from src.environments.cyber_env import CyberDefenseEnv
from src.agent.state import discretize_state
from src.marketplace.ranking import BestPolicyReference
from .stats import ExecutionStats


class BaselinePolicy(Enum):
    """
    Baseline policies for performance comparison.

    Defines simple strategies to compare against reused policies.
    Used to demonstrate that learned policies significantly outperform
    naive approaches.

    Attributes:
        RANDOM: Random action selection at each step
        IGNORE_ALL: Always IGNORE alerts
        BLOCK_ALL: Always BLOCK_IP for any alert
        MONITOR_ONLY: Always MONITOR (minimal intervention)
    """
    RANDOM = "random"  # Random action at each step
    IGNORE_ALL = "ignore_all"  # Always IGNORE alerts
    BLOCK_ALL = "block_all"  # Always BLOCK_IP
    MONITOR_ONLY = "monitor_only"  # Always MONITOR


class PolicyConsumer:
    """
    Consumer that reuses verified policies without training.

    Core component of the policy reuse module. Demonstrates the key
    value proposition: once intelligence is learned and verified,
    it can be reused instantly by any consumer without retraining.

    Responsibilities:
        - Load pre-trained policies from storage
        - Execute policies deterministically (no exploration)
        - Compare performance against baseline strategies
        - Provide performance metrics for evaluation

    Design Principles:
        - Pure execution: no training, verification, or modification
        - Deterministic: same policy + same seed = same results
        - Observable: focuses on measurable performance outcomes
        - Stateless: no persistent state between executions

    Attributes:
        policy_store_dir: Path to directory containing policy artifacts
    """

    def __init__(self, policy_store_dir: str = "policies"):
        """
        Initialize consumer with policy storage location.

        Args:
            policy_store_dir: Path to directory containing policy artifacts.
                Defaults to "policies" in current working directory.
        """
        self.policy_store_dir = Path(policy_store_dir)
    
    def load_policy(self, policy_hash: str) -> Dict:
        """
        Load policy artifact from storage.
        
        Args:
            policy_hash: Hash of the policy to load
            
        Returns:
            Policy dictionary (state -> action mapping)
            
        Raises:
            FileNotFoundError: If policy artifact doesn't exist
            ValueError: If policy is invalid/corrupted
            
        Design:
            Fallback implementation uses local JSON storage.
            Google-first version would fetch from Firebase.
        """
        policy_path = self.policy_store_dir / f"{policy_hash}.json"
        
        if not policy_path.exists():
            raise FileNotFoundError(
                f"Policy artifact not found: {policy_path}\n"
                f"Expected policy hash: {policy_hash}"
            )
        
        try:
            with open(policy_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted policy artifact: {e}")
        
        # Validate structure
        if "policy" not in data:
            raise ValueError("Invalid policy artifact: missing 'policy' key")
        
        policy = data["policy"]
        
        if not isinstance(policy, dict):
            raise ValueError("Invalid policy: must be a dictionary")
        
        if len(policy) == 0:
            raise ValueError("Invalid policy: empty policy")
        
        return policy
    
    def execute_policy(
        self,
        policy: Dict,
        episodes: int = 100,
        seed: Optional[int] = None
    ) -> ExecutionStats:
        """
        Execute policy in simulated cyber defense environment (no training).
        
        Args:
            policy: State -> action mapping
            episodes: Number of episodes to run
            seed: Random seed for reproducibility
            
        Returns:
            ExecutionStats with reward and behavior metrics
            
        Design:
            - Deterministic execution (if seed provided)
            - Greedy policy (no exploration)
            - Same environment as training/verification
            
        Mental Model:
            Execute verified defense policy in simulation.
            No learning. Just follow the decision rules.
        """
        env = CyberDefenseEnv(seed=seed)
        total_reward = 0.0
        total_actions = 0
        action_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}  # IGNORE, MONITOR, RATE_LIMIT, BLOCK_IP, ISOLATE_SERVICE
        system_health_sum = 0.0
        health_readings = 0
        survived_episodes = 0
        
        for _ in range(episodes):
            state = env.reset()
            episode_reward = 0.0
            done = False
            episode_actions = 0
            
            while not done:
                # Track system health
                system_health_sum += state["system_health"]
                health_readings += 1
                
                # Discretize state (same as training)
                discrete_state = discretize_state(state)
                
                # Look up action in policy (greedy)
                action = policy.get(str(discrete_state), 1)  # Default to MONITOR if unseen
                
                # Count actions
                episode_actions += 1
                action_counts[action] += 1
                
                # Execute action
                state, reward, done = env.step(action)
                episode_reward += reward
            
            # Episode stats
            total_reward += episode_reward
            total_actions += episode_actions
            
            # Survival: if system didn't reach CRITICAL state
            if state["system_health"] != 2:  # Not CRITICAL
                survived_episodes += 1
        
        # Compute averages
        avg_reward = total_reward / episodes
        action_percentages = {k: v / total_actions if total_actions > 0 else 0 for k, v in action_counts.items()}
        avg_system_health = system_health_sum / health_readings if health_readings > 0 else 0
        survival_rate = survived_episodes / episodes
        
        return ExecutionStats(
            avg_reward=avg_reward,
            save_percentage=action_percentages[0],  # IGNORE percentage
            use_percentage=action_percentages[3],   # BLOCK_IP percentage
            avg_battery=avg_system_health,  # Renamed but holds system health average
            survival_rate=survival_rate
        )
    
    def execute_baseline(
        self,
        baseline: BaselinePolicy,
        episodes: int = 100,
        seed: Optional[int] = None
    ) -> ExecutionStats:
        """
        Execute baseline policy for performance comparison.

        Runs a simple baseline strategy to provide a performance benchmark
        for evaluating the quality of reused policies.

        Args:
            baseline: Which baseline strategy to execute
            episodes: Number of episodes to run for averaging
            seed: Random seed for environment reproducibility

        Returns:
            ExecutionStats for the baseline

        Raises:
            ValueError: If baseline type is not recognized
        """
        env = CyberDefenseEnv(seed=seed)
        total_reward = 0.0
        total_actions = 0
        action_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        system_health_sum = 0.0
        health_readings = 0
        survived_episodes = 0
        
        for _ in range(episodes):
            state = env.reset()
            episode_reward = 0.0
            done = False
            episode_actions = 0
            
            while not done:
                system_health_sum += state["system_health"]
                health_readings += 1
                
                # Select action based on baseline strategy
                if baseline == BaselinePolicy.RANDOM:
                    action = random.choice([0, 1, 2, 3, 4])  # Random cyber defense action
                elif baseline == BaselinePolicy.IGNORE_ALL:
                    action = 0  # Always IGNORE
                elif baseline == BaselinePolicy.BLOCK_ALL:
                    action = 3  # Always BLOCK_IP
                elif baseline == BaselinePolicy.MONITOR_ONLY:
                    action = 1  # Always MONITOR
                else:
                    raise ValueError(f"Unknown baseline: {baseline}")
                
                episode_actions += 1
                action_counts[action] += 1
                
                # Execute action
                state, reward, done = env.step(action)
                episode_reward += reward
            
            # Episode stats
            total_reward += episode_reward
            total_actions += episode_actions
            
            # Survival check
            if state["system_health"] != 2:  # Not CRITICAL
                survived_episodes += 1
        
        avg_reward = total_reward / episodes
        action_percentages = {k: v / total_actions if total_actions > 0 else 0 for k, v in action_counts.items()}
        avg_system_health = system_health_sum / health_readings if health_readings > 0 else 0
        survival_rate = survived_episodes / episodes
        
        return ExecutionStats(
            avg_reward=avg_reward,
            save_percentage=action_percentages[0],  # IGNORE
            use_percentage=action_percentages[3],   # BLOCK_IP
            avg_battery=avg_system_health,
            survival_rate=survival_rate
        )
    
    def compare_with_baseline(
        self,
        policy: Dict,
        baseline: BaselinePolicy = BaselinePolicy.RANDOM,
        episodes: int = 100,
        seed: Optional[int] = None
    ) -> Tuple[ExecutionStats, ExecutionStats, float]:
        """
        Compare reused policy against baseline.
        
        Args:
            policy: Reused policy
            baseline: Baseline strategy
            episodes: Number of episodes
            seed: Random seed
            
        Returns:
            Tuple of (policy_stats, baseline_stats, improvement_percentage)
            
        Purpose:
            THE WOW MOMENT.
            Show that reuse is better than naive strategies.
            
        Demo:
            "Reused policy: 15.0 defense score"
            "Baseline (random): -5.0 defense score"
            "Improvement: 400%"
        """
        policy_stats = self.execute_policy(policy, episodes, seed)
        baseline_stats = self.execute_baseline(baseline, episodes, seed)
        
        # Calculate improvement percentage
        # Handle both positive and negative rewards properly
        if baseline_stats.avg_reward != 0:
            improvement = ((policy_stats.avg_reward - baseline_stats.avg_reward) / abs(baseline_stats.avg_reward)) * 100
        else:
            # Baseline is exactly 0
            if policy_stats.avg_reward > 0:
                improvement = 100.0
            elif policy_stats.avg_reward < 0:
                improvement = -100.0
            else:
                improvement = 0.0
        
        return policy_stats, baseline_stats, improvement


# Convenience function for simple use cases
def reuse_best_policy(
    best_policy_ref: BestPolicyReference,
    policy_store_dir: str = "policies",
    episodes: int = 100,
    baseline: BaselinePolicy = BaselinePolicy.RANDOM,
    seed: Optional[int] = None
) -> Dict:
    """
    Convenience function for reusing best policy and comparing with baseline.

    High-level function that combines policy loading and baseline comparison
    into a single call. Ideal for marketplace integration and quick evaluations.

    Args:
        best_policy_ref: Reference to best policy from marketplace ranking
        policy_store_dir: Directory path containing policy artifacts
        episodes: Number of episodes to run for performance evaluation
        baseline: Baseline strategy for performance comparison
        seed: Random seed for reproducible results

    Returns:
        Dictionary containing evaluation results with keys:
            - policy_hash: SHA-256 hash of the reused policy
            - agent_id: ID of the agent that created the policy
            - verified_reward: Reward verified by the verification layer
            - policy_reward: Actual reward achieved by reused policy
            - baseline_reward: Reward achieved by baseline strategy
            - improvement: Percentage improvement over baseline
            - baseline_type: String name of baseline strategy used
            - episodes: Number of episodes used for evaluation
    """
    consumer = PolicyConsumer(policy_store_dir)
    
    # Load policy
    policy = consumer.load_policy(best_policy_ref.policy_hash)
    
    # Compare with baseline
    policy_stats, baseline_stats, improvement = consumer.compare_with_baseline(
        policy, baseline, episodes, seed
    )
    
    return {
        "policy_hash": best_policy_ref.policy_hash,
        "agent_id": best_policy_ref.agent_id,
        "verified_reward": best_policy_ref.verified_reward,
        "policy_reward": policy_stats.avg_reward,
        "baseline_reward": baseline_stats.avg_reward,
        "improvement": improvement,
        "baseline_type": baseline.value,
        "episodes": episodes
    }
