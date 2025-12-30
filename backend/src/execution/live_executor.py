"""
Live Policy Execution Monitor
Streams policy decisions step-by-step without learning
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class ExecutionStep:
    """Single step in policy execution"""
    timestep: int
    state: Dict[str, int]
    discrete_state: Tuple[int, ...]
    action: int
    action_name: str
    reward: float
    cumulative_reward: float
    system_health: float
    confidence: float  # Q-value confidence
    entropy: float  # Decision entropy
    attack_severity: int
    alert_confidence: int
    time_elapsed: float


@dataclass
class ExecutionConfig:
    """Configuration for live execution"""
    policy_hash: str
    max_steps: int = 500
    speed_ms: int = 50  # Delay between steps (milliseconds)
    adaptive_pressure: bool = False  # Escalate difficulty over time
    partial_observability: bool = False  # POMDP-like execution
    pressure_rate: float = 1.0  # How fast pressure increases


class AdaptiveEnvironmentPressure:
    """Escalates environment difficulty over time"""
    
    def __init__(self, base_penalty: float = -1.0, escalation_rate: float = 1.0):
        self.base_penalty = base_penalty
        self.escalation_rate = escalation_rate
        self.step_count = 0
    
    def get_penalty_multiplier(self, step: int) -> float:
        """Returns penalty multiplier based on step"""
        # Gradually increase penalty severity
        return 1.0 + (step / 500.0) * self.escalation_rate
    
    def get_attack_duration_bonus(self, step: int) -> int:
        """Attacks last longer as time progresses"""
        # Every 100 steps, attacks become 1 unit longer
        return min(2, step // 100)
    
    def apply_pressure(self, reward: float, step: int) -> float:
        """Apply escalating pressure to rewards"""
        if reward < 0:
            multiplier = self.get_penalty_multiplier(step)
            return reward * multiplier
        return reward


class PartialObservabilityFilter:
    """Simulates partial observability (POMDP-like)"""
    
    def __init__(self):
        self.last_state = None
        self.observation_noise = 0.1
    
    def filter_observation(self, full_state: Tuple[int, ...]) -> Tuple[int, ...]:
        """Agent sees limited state, verification sees all"""
        # Store full state for verification
        self.last_state = full_state
        
        # Agent only sees partial information with noise
        # For cyber defense: hide some attack details
        attack_severity, system_health, response_time, alert_confidence, _ = full_state
        
        # Obscure exact attack severity (±1 level with some probability)
        if np.random.random() < self.observation_noise:
            attack_severity = max(0, min(2, attack_severity + np.random.choice([-1, 0, 1])))
        
        # Hide response time completely (must infer from context)
        response_time = 1  # Always appears "medium"
        
        return (attack_severity, system_health, response_time, alert_confidence, full_state[4])
    
    def get_full_state(self) -> Tuple[int, ...]:
        """Verification gets full state"""
        return self.last_state


class PolicyConfidenceCalculator:
    """Calculates policy confidence from Q-values"""
    
    def __init__(self):
        """Initialize with policy statistics"""
        self.policy_stats = None
    
    def analyze_policy(self, policy: Dict) -> None:
        """Analyze policy to compute statistics for confidence calculation"""
        if not policy:
            self.policy_stats = {"coverage": 0.0, "action_diversity": 1.0}
            print("  [Confidence] No policy to analyze")
            return
        
        # Calculate action distribution
        action_counts = {}
        for action in policy.values():
            action_counts[action] = action_counts.get(action, 0) + 1
        
        total_states = len(policy)
        action_distribution = {a: c/total_states for a, c in action_counts.items()}
        
        # Calculate diversity (entropy of action distribution)
        diversity = 0.0
        for prob in action_distribution.values():
            if prob > 0:
                diversity -= prob * np.log(prob)
        
        # Normalize by max entropy (log of 5 actions)
        max_entropy = np.log(5)
        diversity_normalized = diversity / max_entropy if max_entropy > 0 else 1.0
        
        # Coverage: how many states the policy covers (out of 108 possible for cyber defense)
        max_states = 3 * 3 * 3 * 2 * 2  # 108 possible discrete states
        coverage = min(1.0, total_states / max_states)
        
        self.policy_stats = {
            "coverage": coverage,
            "action_diversity": diversity_normalized,
            "action_distribution": action_distribution,
            "total_states": total_states
        }
        
        print(f"  [Confidence] Policy analyzed: {total_states} states, coverage={coverage:.2%}, diversity={diversity_normalized:.3f}")
        print(f"  [Confidence] Action distribution: {action_distribution}")
    
    def calculate_confidence(self, q_values: List[float]) -> Tuple[float, float]:
        """
        Returns (confidence, entropy)
        
        Confidence: Gap between best and second-best action
        Entropy: Shannon entropy of softmax distribution
        """
        if not q_values or len(q_values) < 2:
            return 0.0, 1.0
        
        # Check if all values are the same (unseen state)
        if len(set(q_values)) == 1:
            return 0.0, 1.0  # No confidence, maximum entropy
        
        # Sort Q-values
        sorted_q = sorted(q_values, reverse=True)
        
        # Confidence: difference between top 2 actions
        # Higher gap = more confident
        gap = sorted_q[0] - sorted_q[1] if len(sorted_q) > 1 else abs(sorted_q[0])
        confidence = max(0.0, min(1.0, gap / 10.0))  # Normalize to [0, 1]
        
        # Entropy: measure of decision uncertainty
        # Convert Q-values to probabilities via softmax with temperature
        temperature = 1.0
        q_array = np.array(q_values)
        q_array = (q_array - np.max(q_array)) / temperature  # Numerical stability
        exp_q = np.exp(q_array)
        probs = exp_q / np.sum(exp_q)
        
        # Shannon entropy
        epsilon = 1e-10
        entropy = -np.sum(probs * np.log(probs + epsilon))
        
        # Normalize entropy (max entropy for 5 actions is log(5))
        max_entropy = np.log(5)
        normalized_entropy = entropy / max_entropy
        
        return float(confidence), float(normalized_entropy)
    
    def get_q_values_for_state(self, policy: Dict, state: str, num_actions: int = 5) -> List[float]:
        """Get Q-values for all actions in a state"""
        if state in policy:
            # State is in policy - high confidence
            best_action = policy[state]
            q_values = [0.0] * num_actions
            
            # Best action gets high Q-value
            q_values[best_action] = 10.0
            
            # Use policy statistics to determine other action values
            if self.policy_stats:
                coverage = self.policy_stats["coverage"]
                diversity = self.policy_stats["action_diversity"]
                
                # Amplify differences for better visibility
                # Square diversity and take power of coverage to make differences more pronounced
                confidence_factor = (coverage ** 1.5) * ((1.0 - diversity) ** 2)
                
                # Other actions get lower values based on confidence
                # Higher confidence = bigger gap between best and other actions
                base_value = 2.0 * (1.0 - confidence_factor) ** 0.7
                spread = 3.0 * (1.0 - confidence_factor) ** 0.8
                
                for i in range(num_actions):
                    if i != best_action:
                        # Deterministic values based on action index
                        q_values[i] = base_value + spread * (i / num_actions)
            else:
                # Default: moderate confidence
                for i in range(num_actions):
                    if i != best_action:
                        q_values[i] = 3.0 + (i * 1.0)
            
            return q_values
        else:
            # Unseen state: Use policy's learned action preferences
            # This shows what the policy "would probably do" based on its training
            if self.policy_stats and "action_distribution" in self.policy_stats:
                action_dist = self.policy_stats["action_distribution"]
                coverage = self.policy_stats["coverage"]
                
                # Base confidence for unseen states (lower than seen states)
                # But NOT zero - we can infer from action preferences
                base_confidence = 0.3 + (coverage * 0.4)  # 0.3-0.7 range
                
                # Create Q-values reflecting action preferences
                q_values = []
                max_prob = max(action_dist.values()) if action_dist else 0.2
                
                for action_idx in range(num_actions):
                    # Get this action's probability in the policy
                    action_prob = action_dist.get(action_idx, 0.0)
                    
                    # Scale Q-value by probability and base confidence
                    # Most preferred action gets highest Q-value
                    q_value = 3.0 + (action_prob / max_prob) * 5.0 * base_confidence
                    q_values.append(q_value)
                
                return q_values
            else:
                # Fallback: slight preference variation
                return [2.0, 2.5, 3.0, 3.5, 4.0]


class LivePolicyExecutor:
    """Executes policy and streams decisions in real-time"""
    
    def __init__(self, env, policy: Dict, config: ExecutionConfig):
        self.env = env
        self.policy = policy
        self.config = config
        self.action_names = ["IGNORE", "MONITOR", "RATE_LIMIT", "BLOCK_IP", "ISOLATE"]
        
        # Optional features
        self.pressure = AdaptiveEnvironmentPressure(
            escalation_rate=config.pressure_rate
        ) if config.adaptive_pressure else None
        
        self.po_filter = PartialObservabilityFilter() if config.partial_observability else None
        
        # Initialize confidence calculator and analyze policy
        self.confidence_calc = PolicyConfidenceCalculator()
        self.confidence_calc.analyze_policy(policy)
        
        # Execution state
        self.steps: List[ExecutionStep] = []
        self.start_time = None
    
    def _discretize_state(self, state) -> Tuple[int, ...]:
        """Convert continuous state to discrete bins"""
        # State is already discrete from CyberDefenseEnv
        # Extract values from dictionary
        attack_severity = int(state.get("attack_severity", 0))
        system_health = int(state.get("system_health", 0))
        attack_type = int(state.get("attack_type", 0))  # Used as response_time proxy
        alert_confidence = int(state.get("alert_confidence", 0))
        time_under_attack = int(state.get("time_under_attack", 0))
        
        # Map to expected discrete ranges
        # attack_severity: 0-2 (LOW, MEDIUM, HIGH)
        # system_health: 0-2 (HEALTHY, DEGRADED, CRITICAL)
        # attack_type as response_time: 0-2
        # alert_confidence: 0-1 (LOW, HIGH)
        # time_under_attack: 0-1 (SHORT, LONG)
        
        return (attack_severity, system_health, attack_type, alert_confidence, time_under_attack)
    
    def _select_action(self, discrete_state: Tuple[int, ...]) -> int:
        """Select action based on policy (no learning)"""
        state_str = str(discrete_state)
        
        # If using partial observability, filter the state
        if self.po_filter:
            agent_state = self.po_filter.filter_observation(discrete_state)
            state_str = str(agent_state)
        
        # Use policy if state is known
        if state_str in self.policy:
            return self.policy[state_str]
        else:
            # For unseen states: Use policy's learned action preferences
            # This makes each policy behave differently based on its training
            if self.confidence_calc.policy_stats and "action_distribution" in self.confidence_calc.policy_stats:
                action_dist = self.confidence_calc.policy_stats["action_distribution"]
                
                # Get Q-values based on action preferences
                q_values = self.confidence_calc.get_q_values_for_state(
                    self.policy, state_str, len(self.action_names)
                )
                
                # Choose action with highest Q-value (greedy)
                return int(np.argmax(q_values))
            else:
                # Final fallback: intelligent heuristics
                attack_severity, system_health, _, alert_confidence, _ = discrete_state
                
                if system_health == 2:  # Critical
                    return 4  # ISOLATE
                elif attack_severity == 2 and alert_confidence == 1:
                    return 3  # BLOCK_IP
                elif attack_severity >= 1:
                    return 2  # RATE_LIMIT
                else:
                    return 1  # MONITOR
    
    def _calculate_metrics(self, discrete_state: Tuple[int, ...], action: int) -> Tuple[float, float]:
        """Calculate confidence and entropy for current decision"""
        state_str = str(discrete_state)
        q_values = self.confidence_calc.get_q_values_for_state(
            self.policy, state_str, len(self.action_names)
        )
        return self.confidence_calc.calculate_confidence(q_values)
    
    def execute_step(self, step: int, state, cumulative_reward: float) -> ExecutionStep:
        """Execute single step and return execution data"""
        # Discretize state
        discrete_state = self._discretize_state(state)
        
        # Select action (deterministic, no learning)
        action = self._select_action(discrete_state)
        
        # Calculate confidence and entropy
        confidence, entropy = self._calculate_metrics(discrete_state, action)
        
        # Take action in environment (returns 3-tuple: next_state, reward, done)
        next_state, reward, done = self.env.step(action)
        
        # Apply adaptive pressure if enabled
        if self.pressure:
            reward = self.pressure.apply_pressure(reward, step)
        
        # Calculate system health percentage
        system_health_pct = (discrete_state[1] / 2.0) * 100
        
        # Record step
        execution_step = ExecutionStep(
            timestep=step,
            state={
                "attack_severity": int(discrete_state[0]),
                "system_health": int(discrete_state[1]),
                "response_time": int(discrete_state[2]),
                "alert_confidence": int(discrete_state[3]),
                "attack_duration": int(discrete_state[4])
            },
            discrete_state=discrete_state,
            action=int(action),
            action_name=self.action_names[action],
            reward=float(reward),
            cumulative_reward=float(cumulative_reward + reward),
            system_health=float(system_health_pct),
            confidence=float(confidence),
            entropy=float(entropy),
            attack_severity=int(discrete_state[0]),
            alert_confidence=int(discrete_state[3]),
            time_elapsed=time.time() - self.start_time if self.start_time else 0.0
        )
        
        return execution_step, next_state, done
    
    async def execute_streaming(self, websocket):
        """Execute policy and stream results via WebSocket"""
        self.start_time = time.time()
        state = self.env.reset()
        cumulative_reward = 0.0
        
        # Send initial configuration
        await websocket.send_json({
            "type": "execution_start",
            "config": {
                "policy_hash": self.config.policy_hash,
                "max_steps": self.config.max_steps,
                "adaptive_pressure": self.config.adaptive_pressure,
                "partial_observability": self.config.partial_observability,
                "speed_ms": self.config.speed_ms
            }
        })
        
        for step in range(self.config.max_steps):
            # Execute step
            execution_step, state, done = self.execute_step(step, state, cumulative_reward)
            cumulative_reward = execution_step.cumulative_reward
            self.steps.append(execution_step)
            
            # Stream step data
            await websocket.send_json({
                "type": "execution_step",
                "data": asdict(execution_step)
            })
            
            # Delay for visualization
            await asyncio.sleep(self.config.speed_ms / 1000.0)
            
            if done:
                break
        
        # Send completion
        await websocket.send_json({
            "type": "execution_complete",
            "summary": {
                "total_steps": len(self.steps),
                "final_reward": cumulative_reward,
                "avg_confidence": float(np.mean([s.confidence for s in self.steps])),
                "avg_entropy": float(np.mean([s.entropy for s in self.steps])),
                "execution_time": time.time() - self.start_time
            }
        })
    
    def execute_batch(self) -> List[ExecutionStep]:
        """Execute full episode and return all steps (for replay)"""
        self.start_time = time.time()
        state = self.env.reset()
        cumulative_reward = 0.0
        
        for step in range(self.config.max_steps):
            execution_step, state, done = self.execute_step(step, state, cumulative_reward)
            cumulative_reward = execution_step.cumulative_reward
            self.steps.append(execution_step)
            
            if done:
                break
        
        return self.steps


import asyncio
