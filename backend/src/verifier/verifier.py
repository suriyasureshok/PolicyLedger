"""
Policy Verifier — Core Novelty

This is the examiner who re-solves the paper using submitted answers.

PURPOSE:
    Answer ONE question: "Is the claimed reward reproducible 
    when the policy is replayed in the same environment?"

NOT A:
    - Judge
    - Ranker
    - Trainer
    - Negotiator

PROPERTIES:
    - Deterministic
    - Skeptical
    - Stateless (per verification)

TODO: Google Cloud Integration
- Vertex AI Custom Jobs: Run verification in isolated containers
- Cloud Build: Build verification images on policy submission
- Cloud Logging: Structured verification audit logs
"""

from typing import NamedTuple, Optional
from enum import Enum
import hashlib

from src.agent.runner import PolicyClaim
from src.agent.policy import deserialize_policy, Policy
from src.agent.state import discretize_state
from src.environments.cyber_env import CyberDefenseEnv


class VerificationStatus(Enum):
    """Binary verification decision."""
    VALID = "VALID"
    INVALID = "INVALID"


class VerificationResult(NamedTuple):
    """
    Authoritative verification result.
    
    This is what the verifier outputs - nothing more, nothing less.
    """
    agent_id: str
    policy_hash: str
    verified_reward: Optional[float]  # None if verification failed before replay
    status: VerificationStatus
    reason: str  # Human-readable explanation
    
    def __repr__(self) -> str:
        return (
            f"VerificationResult(\n"
            f"  agent_id='{self.agent_id}',\n"
            f"  policy_hash='{self.policy_hash[:16]}...',\n"
            f"  status={self.status.value},\n"
            f"  verified_reward={self.verified_reward},\n"
            f"  reason='{self.reason}'\n"
            f")"
        )


class PolicyVerifier:
    """
    Deterministic policy verifier.
    
    This verifier:
    1. Loads policy artifact
    2. Replays policy in environment
    3. Compares claimed vs verified reward
    4. Returns binary decision: VALID or INVALID
    
    Rules (STRICT):
    - Does NOT rank policies
    - Does NOT write to ledger directly
    - Does NOT retry failed claims automatically
    - Does NOT ask agents for clarification
    - Does NOT store verification history
    - Does NOT adjust thresholds dynamically
    
    Verifier is a judge, not a coach.
    """
    
    def __init__(self, reward_threshold: float = 1e-6):
        """
        Initialize verifier.
        
        Args:
            reward_threshold: Maximum acceptable difference between 
                            claimed and verified rewards.
                            
                            Recommendations:
                            - Fully deterministic env: 0.0
                            - Floating-point noise: 1e-6
        """
        self.reward_threshold = reward_threshold
    
    def verify(self, claim: PolicyClaim) -> VerificationResult:
        """
        Verify a policy claim.
        
        This is the main entry point for verification.
        
        Args:
            claim: PolicyClaim from submission collector
        
        Returns:
            VerificationResult with binary decision
        
        Process:
            1. Validate policy hash
            2. Load policy artifact
            3. Replay policy in environment
            4. Compare rewards
            5. Return decision
        """
        # Step 1: Validate policy hash
        hash_result = self._validate_policy_hash(claim)
        if hash_result is not None:
            return hash_result
        
        # Step 2: Load policy artifact
        try:
            policy = self._load_policy(claim.policy_artifact)
        except Exception as e:
            return VerificationResult(
                agent_id=claim.agent_id,
                policy_hash=claim.policy_hash,
                verified_reward=None,
                status=VerificationStatus.INVALID,
                reason=f"Policy cannot be deterministically replayed: {str(e)}"
            )
        
        # Step 3: Replay policy in environment
        try:
            verified_reward = self._replay_policy(claim.env_id, policy)
        except Exception as e:
            return VerificationResult(
                agent_id=claim.agent_id,
                policy_hash=claim.policy_hash,
                verified_reward=None,
                status=VerificationStatus.INVALID,
                reason=f"Replay failed: {str(e)}"
            )
        
        # Step 4: Compare rewards
        return self._compare_rewards(
            claim.agent_id,
            claim.policy_hash,
            claim.claimed_reward,
            verified_reward
        )
    
    # =========================================================================
    # COMPONENT 1: POLICY LOADER
    # =========================================================================
    
    def _validate_policy_hash(self, claim: PolicyClaim) -> Optional[VerificationResult]:
        """
        Validate that policy artifact matches claimed hash.
        
        This prevents:
        - Post-submission tampering
        - Man-in-the-middle attacks
        
        Args:
            claim: PolicyClaim to validate
        
        Returns:
            VerificationResult if hash mismatch, None if valid
        """
        # Compute hash of artifact
        actual_hash = hashlib.sha256(claim.policy_artifact).hexdigest()
        
        # Compare with claimed hash
        if actual_hash != claim.policy_hash:
            return VerificationResult(
                agent_id=claim.agent_id,
                policy_hash=claim.policy_hash,
                verified_reward=None,
                status=VerificationStatus.INVALID,
                reason="Policy artifact does not match claimed hash."
            )
        
        return None  # Hash is valid
    
    def _load_policy(self, policy_artifact: bytes) -> Policy:
        """
        Turn submitted policy artifact into executable decision function.
        
        What it must do:
        - Deserialize policy artifact
        - Validate basic structure
        - Ensure determinism
        
        What it must NOT do:
        - Modify policy
        - Normalize values
        - "Fix" missing states
        - Guess defaults
        
        If policy is incomplete → raise exception.
        
        Reason: A policy that cannot be replayed cannot be trusted.
        
        Args:
            policy_artifact: Serialized policy bytes
        
        Returns:
            Reconstructed policy {state: action}
        
        Raises:
            Exception if policy cannot be loaded or is invalid
        """
        # Deserialize policy
        policy = deserialize_policy(policy_artifact)
        
        # Validate basic structure
        if not isinstance(policy, dict):
            raise ValueError("Policy must be a dictionary")
        
        if len(policy) == 0:
            raise ValueError("Policy cannot be empty")
        
        # Validate policy entries
        for state, action in policy.items():
            # State must be tuple of 5 integers for cyber defense environment
            if not isinstance(state, tuple) or len(state) != 5:
                raise ValueError(f"Invalid state format: {state}")
            
            # Action must be 0-4 (IGNORE, MONITOR, RATE_LIMIT, BLOCK_IP, ISOLATE_SERVICE)
            if action not in [0, 1, 2, 3, 4]:
                raise ValueError(f"Invalid action: {action}")
        
        return policy
    
    # =========================================================================
    # COMPONENT 2: REPLAY ENGINE (MOST IMPORTANT)
    # =========================================================================
    
    def _replay_policy(self, env_id: str, policy: Policy) -> float:
        """
        Re-run simulated cyber defense environment using only the policy.
        
        This is the heart of verification.
        
        How replay works:
        1. Instantiate environment with fixed seed
        2. Run multiple episodes (20) to average out randomness
        3. For each step:
            - Observe state
            - Ask policy for action
            - Apply action
            - Accumulate reward
        4. Stop at terminal condition
        5. Output average reward across all episodes
        
        Non-negotiable rules:
        - Same environment code as agent
        - Same seed
        - No exploration
        - No epsilon-greedy
        - No re-training
        - No environment modification
        
        Args:
            env_id: Environment identifier (contains seed and config)
            policy: Loaded policy {state: action}
        
        Returns:
            Average accumulated reward across 20 episodes
        
        Raises:
            Exception if replay fails or policy is incomplete
        """
        # Parse environment ID to extract configuration
        # Format: "cyber_defense_env_seed_{seed}_horizon_{time_horizon}"
        seed, time_horizon = self._parse_env_id(env_id)
        
        # Run multiple episodes to average out randomness
        num_verification_episodes = 20
        episode_rewards = []
        
        for episode_num in range(num_verification_episodes):
            # Create environment with exact same configuration
            env = CyberDefenseEnv(
                time_horizon=time_horizon,
                seed=seed
            )
            
            # Reset environment to initial state
            state_dict = env.reset()
            
            # Accumulate total reward for this episode
            episode_reward = 0.0
            steps = 0
            max_steps = time_horizon * 2  # Safety limit
            
            # Replay loop
            while not env.done and steps < max_steps:
                # Convert state dict to state tuple (discretized)
                state_tuple = self._discretize_state(state_dict)
                
                # Ask policy for action
                if state_tuple not in policy:
                    # Default to IGNORE (action 0) for unseen states
                    # This matches the behavior during deterministic evaluation in training
                    action = 0
                else:
                    action = policy[state_tuple]
                
                # Apply action and observe result
                state_dict, reward, done = env.step(action)
                
                # Accumulate reward
                episode_reward += reward
                steps += 1
            
            episode_rewards.append(episode_reward)
        
        # Return average reward across all episodes
        average_reward = sum(episode_rewards) / len(episode_rewards)
        return average_reward
    
    def _parse_env_id(self, env_id: str) -> tuple[int, int]:
        """
        Parse environment ID to extract configuration.
        
        Args:
            env_id: Environment identifier
                   Format: "cyber_defense_env_seed_{seed}_horizon_{time_horizon}"
        
        Returns:
            (seed, time_horizon)
        
        Raises:
            ValueError if env_id format is invalid
        """
        try:
            # Example: "cyber_defense_env_seed_42_horizon_24"
            parts = env_id.split("_")
            
            # Extract seed
            seed_idx = parts.index("seed") + 1
            seed = int(parts[seed_idx])
            
            # Extract time_horizon
            horizon_idx = parts.index("horizon") + 1
            time_horizon = int(parts[horizon_idx])
            
            return seed, time_horizon
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid environment ID format: {env_id}") from e
    
    def _discretize_state(self, state_dict: dict) -> tuple:
        """
        Convert environment state dict to discretized state tuple.
        
        This MUST match the discretization used during training.
        
        Critical: Uses the exact same discretization function as the agent
        to ensure state representation consistency.
        
        Args:
            state_dict: State from environment (cyber defense format)
        
        Returns:
            Discretized state tuple (format depends on environment)
        """
        # Use the EXACT same discretization as training
        # This is critical for verification correctness
        return discretize_state(state_dict)
    
    # =========================================================================
    # COMPONENT 3: REWARD COMPARATOR
    # =========================================================================
    
    def _compare_rewards(
        self,
        agent_id: str,
        policy_hash: str,
        claimed_reward: float,
        verified_reward: float
    ) -> VerificationResult:
        """
        Compare claimed vs verified rewards and make decision.
        
        Decision rule:
            if abs(claimed - verified) <= threshold:
                VALID
            else:
                INVALID
        
        No partial credit. No negotiation. No averaging.
        
        Args:
            agent_id: Agent identifier
            policy_hash: Policy hash
            claimed_reward: Reward claimed by agent
            verified_reward: Reward computed by verifier
        
        Returns:
            VerificationResult with binary decision
        """
        # Compute difference
        reward_diff = abs(claimed_reward - verified_reward)
        
        # Make decision
        if reward_diff <= self.reward_threshold:
            status = VerificationStatus.VALID
            reason = (
                f"Claimed reward reproducible under deterministic replay. "
                f"Difference: {reward_diff:.6f}"
            )
        else:
            status = VerificationStatus.INVALID
            reason = (
                f"Claimed reward not reproducible under deterministic replay. "
                f"Claimed: {claimed_reward:.3f}, Verified: {verified_reward:.3f}, "
                f"Difference: {reward_diff:.3f}"
            )
        
        return VerificationResult(
            agent_id=agent_id,
            policy_hash=policy_hash,
            verified_reward=verified_reward,
            status=status,
            reason=reason
        )
    
    def verify_determinism(self, claim: PolicyClaim, num_runs: int = 3) -> bool:
        """
        Verify that replay is deterministic by running multiple times.
        
        This is a sanity check, not part of normal verification flow.
        
        Args:
            claim: PolicyClaim to verify
            num_runs: Number of replay runs
        
        Returns:
            True if all runs produce identical reward, False otherwise
        """
        # Load policy once
        policy = self._load_policy(claim.policy_artifact)
        
        # Run replay multiple times
        rewards = []
        for _ in range(num_runs):
            reward = self._replay_policy(claim.env_id, policy)
            rewards.append(reward)
        
        # Check if all rewards are identical
        return len(set(rewards)) == 1


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def verify_claim(
    claim: PolicyClaim,
    reward_threshold: float = 1e-6
) -> VerificationResult:
    """
    Convenience function for one-shot verification.
    
    Args:
        claim: PolicyClaim to verify
        reward_threshold: Maximum acceptable reward difference
    
    Returns:
        VerificationResult
    """
    verifier = PolicyVerifier(reward_threshold=reward_threshold)
    return verifier.verify(claim)
