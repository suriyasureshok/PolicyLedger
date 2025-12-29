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
- src.shared.env: EnergySlotEnv for simulation environment
- src.agent.state: discretize_state for state processing
- src.marketplace.ranking: BestPolicyReference for policy selection

Author: Your Name
Created: 2025-12-28
"""

import json
from pathlib import Path
from typing import Dict, Tuple, Optional
from enum import Enum
import random

from src.shared.env import EnergySlotEnv
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
        ALWAYS_SAVE: Always choose SAVE action
        ALWAYS_USE: Always choose USE action
    """
    RANDOM = "random"  # Random action at each step
    ALWAYS_SAVE = "always_save"  # Always choose SAVE
    ALWAYS_USE = "always_use"  # Always choose USE


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
        Execute policy in environment (no training).
        
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
            Execute topper's answers in exam.
            No learning. Just follow the script.
        """
        env = EnergySlotEnv(seed=seed)
        total_reward = 0.0
        total_actions = 0
        save_count = 0
        use_count = 0
        total_battery = 0.0
        battery_readings = 0
        survived_episodes = 0
        
        for _ in range(episodes):
            state = env.reset()
            episode_reward = 0.0
            done = False
            episode_actions = 0
            episode_save = 0
            episode_use = 0
            episode_battery = 0.0
            episode_battery_count = 0
            
            while not done:
                # Track battery
                battery = state["battery_level"]
                episode_battery += battery
                episode_battery_count += 1
                
                # Discretize state (same as training)
                discrete_state = discretize_state(state)
                
                # Look up action in policy (greedy)
                action = policy.get(str(discrete_state), 0)  # Default to SAVE if unseen
                
                # Count actions
                episode_actions += 1
                if action == 0:  # SAVE
                    episode_save += 1
                elif action == 1:  # USE
                    episode_use += 1
                
                # Execute action
                state, reward, done = env.step(action)
                episode_reward += reward
            
            # Episode stats
            total_reward += episode_reward
            total_actions += episode_actions
            save_count += episode_save
            use_count += episode_use
            total_battery += episode_battery
            battery_readings += episode_battery_count
            
            # Survival: if done by reaching time_slots (not battery exhaustion)
            if done and state["battery_level"] > 0:  # Assuming done and battery >0 means survived
                survived_episodes += 1
        
        # Compute averages
        avg_reward = total_reward / episodes
        save_percentage = save_count / total_actions if total_actions > 0 else 0
        use_percentage = use_count / total_actions if total_actions > 0 else 0
        avg_battery = total_battery / battery_readings if battery_readings > 0 else 0
        survival_rate = survived_episodes / episodes
        
        return ExecutionStats(
            avg_reward=avg_reward,
            save_percentage=save_percentage,
            use_percentage=use_percentage,
            avg_battery=avg_battery,
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
        env = EnergySlotEnv(seed=seed)
        total_reward = 0.0
        total_actions = 0
        save_count = 0
        use_count = 0
        total_battery = 0.0
        battery_readings = 0
        survived_episodes = 0
        
        for _ in range(episodes):
            state = env.reset()
            episode_reward = 0.0
            done = False
            episode_actions = 0
            episode_save = 0
            episode_use = 0
            episode_battery = 0.0
            episode_battery_count = 0
            
            while not done:
                battery = state["battery_level"]
                episode_battery += battery
                episode_battery_count += 1
                
                # Select action based on baseline strategy
                if baseline == BaselinePolicy.RANDOM:
                    action = random.choice([0, 1])  # Random
                elif baseline == BaselinePolicy.ALWAYS_SAVE:
                    action = 0  # Always SAVE
                elif baseline == BaselinePolicy.ALWAYS_USE:
                    action = 1  # Always USE
                else:
                    raise ValueError(f"Unknown baseline: {baseline}")
                
                episode_actions += 1
                if action == 0:
                    episode_save += 1
                elif action == 1:
                    episode_use += 1
                
                state, reward, done = env.step(action)
                episode_reward += reward
            
            total_reward += episode_reward
            total_actions += episode_actions
            save_count += episode_save
            use_count += episode_use
            total_battery += episode_battery
            battery_readings += episode_battery_count
            
            if done and state["battery_level"] > 0:
                survived_episodes += 1
        
        avg_reward = total_reward / episodes
        save_percentage = save_count / total_actions if total_actions > 0 else 0
        use_percentage = use_count / total_actions if total_actions > 0 else 0
        avg_battery = total_battery / battery_readings if battery_readings > 0 else 0
        survival_rate = survived_episodes / episodes
        
        return ExecutionStats(
            avg_reward=avg_reward,
            save_percentage=save_percentage,
            use_percentage=use_percentage,
            avg_battery=avg_battery,
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
            Show that reuse is better than ignorance.
            
        Demo:
            "Reused policy: 15.0"
            "Baseline (random): 5.0"
            "Improvement: 200%"
        """
        policy_stats = self.execute_policy(policy, episodes, seed)
        baseline_stats = self.execute_baseline(baseline, episodes, seed)
        
        # Calculate improvement percentage
        if baseline_stats.avg_reward > 0:
            improvement = ((policy_stats.avg_reward - baseline_stats.avg_reward) / baseline_stats.avg_reward) * 100
        elif baseline_stats.avg_reward < 0 and policy_stats.avg_reward > 0:
            # Policy went from negative to positive - infinite improvement
            improvement = float('inf')
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
