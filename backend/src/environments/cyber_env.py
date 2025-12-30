"""
Cyber Defense Environment — Deterministic Decision-Level Simulation

This environment simulates cybersecurity incident response at the DECISION level,
NOT the packet or system level. The agent must choose defensive actions based on
attack indicators to maximize damage prevention while minimizing operational costs.

This is a SIMULATION for demonstrating RL policy verification, not a real defense system.
"""

from typing import Dict, Tuple
import numpy as np
from src.environments.base_env import BaseEnv


class CyberDefenseEnv(BaseEnv):
    """
    Deterministic cybersecurity decision-policy simulation.
    
    The agent observes attack indicators and system state, then chooses defensive
    actions. Rewards reflect damage prevented vs. operational costs.
    
    STATE SPACE (discrete):
        - attack_severity: LOW (0) | MEDIUM (1) | HIGH (2)
        - attack_type: SCAN (0) | BRUTE_FORCE (1) | DOS (2)
        - system_health: HEALTHY (0) | DEGRADED (1) | CRITICAL (2)
        - alert_confidence: LOW (0) | HIGH (1)
        - time_under_attack: SHORT (0) | LONG (1)
    
    ACTION SPACE:
        - IGNORE (0): No action taken
        - MONITOR (1): Enhanced logging and observation
        - RATE_LIMIT (2): Throttle suspicious traffic
        - BLOCK_IP (3): Block suspected source IPs
        - ISOLATE_SERVICE (4): Quarantine affected service
    
    REWARD FUNCTION:
        Positive: Damage prevented by appropriate responses
        Negative: False positives, service disruption, ignored severe attacks
        
        This reward structure exposes unsafe policies during verification.
    
    DETERMINISM:
        - Fixed seed controls all randomness
        - Same seed + same actions = same trajectory
        - Critical for verification replay
    """
    
    # Action constants
    IGNORE = 0
    MONITOR = 1
    RATE_LIMIT = 2
    BLOCK_IP = 3
    ISOLATE_SERVICE = 4
    
    # State value constants
    SEVERITY_LOW = 0
    SEVERITY_MEDIUM = 1
    SEVERITY_HIGH = 2
    
    TYPE_SCAN = 0
    TYPE_BRUTE_FORCE = 1
    TYPE_DOS = 2
    
    HEALTH_HEALTHY = 0
    HEALTH_DEGRADED = 1
    HEALTH_CRITICAL = 2
    
    CONFIDENCE_LOW = 0
    CONFIDENCE_HIGH = 1
    
    TIME_SHORT = 0
    TIME_LONG = 1
    
    def __init__(
        self,
        time_horizon: int = 24,
        seed: int = 42,
    ):
        """
        Initialize cyber defense environment.
        
        Args:
            time_horizon: Number of time steps in episode (simulation duration)
            seed: Random seed for deterministic behavior
        """
        self.time_horizon = time_horizon
        self.seed = seed
        
        # Initialize RNG for deterministic randomness
        self._rng = np.random.RandomState(seed)
        
        # Generate deterministic attack scenario
        self._generate_attack_scenario()
        
        # Reset to initial state
        self.reset()
    
    def _generate_attack_scenario(self) -> None:
        """
        Generate a deterministic attack scenario based on seed.
        
        This creates a realistic but fully reproducible sequence of attack
        indicators that the agent must respond to. The scenario includes:
        - Attack type evolution
        - Severity escalation patterns
        - Confidence level changes
        
        Rules:
            - Fully deterministic given seed
            - Same seed → same scenario
            - No randomness after initialization
        """
        # Generate attack severity progression (0=LOW, 1=MEDIUM, 2=HIGH)
        # Start low, potentially escalate
        severity_base = self._rng.choice([0, 1, 2], size=self.time_horizon, p=[0.5, 0.3, 0.2])
        self.severity_schedule = severity_base.copy()
        
        # Add escalation patterns (attacks can intensify if not addressed)
        for i in range(1, self.time_horizon):
            if self.severity_schedule[i-1] == 2:  # Previous was HIGH
                if self._rng.random() < 0.6:  # 60% chance to stay HIGH
                    self.severity_schedule[i] = 2
        
        # Generate attack types (0=SCAN, 1=BRUTE_FORCE, 2=DOS)
        self.attack_type_schedule = self._rng.choice([0, 1, 2], size=self.time_horizon, p=[0.4, 0.4, 0.2])
        
        # Generate alert confidence (0=LOW, 1=HIGH)
        # Higher severity attacks have higher confidence
        self.confidence_schedule = np.zeros(self.time_horizon, dtype=int)
        for i in range(self.time_horizon):
            if self.severity_schedule[i] == 2:  # HIGH severity
                self.confidence_schedule[i] = 1 if self._rng.random() < 0.8 else 0
            elif self.severity_schedule[i] == 1:  # MEDIUM severity
                self.confidence_schedule[i] = 1 if self._rng.random() < 0.5 else 0
            else:  # LOW severity
                self.confidence_schedule[i] = 1 if self._rng.random() < 0.3 else 0
    
    def reset(self) -> Dict:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observable state
        """
        self.current_step = 0
        self.system_health = self.HEALTH_HEALTHY
        self.time_under_attack = self.TIME_SHORT
        self.done = False
        self.consecutive_attacks = 0
        self.damage_accumulated = 0.0
        
        return self._get_state()
    
    def step(self, action: int) -> Tuple[Dict, float, bool]:
        """
        Execute defensive action and advance simulation by one time step.
        
        Args:
            action: Defense action (0-4)
        
        Returns:
            Tuple of (next_state, reward, done)
        
        Raises:
            RuntimeError: If episode already terminated
            ValueError: If action is invalid
        """
        if self.done:
            raise RuntimeError("Episode has terminated. Call reset().")
        
        if action not in [self.IGNORE, self.MONITOR, self.RATE_LIMIT, 
                         self.BLOCK_IP, self.ISOLATE_SERVICE]:
            raise ValueError(f"Invalid action: {action}")
        
        # Get current attack state
        severity = self.severity_schedule[self.current_step]
        attack_type = self.attack_type_schedule[self.current_step]
        confidence = self.confidence_schedule[self.current_step]
        
        # Calculate reward based on action appropriateness
        reward = self._calculate_reward(action, severity, attack_type, confidence)
        
        # Update system state based on action and attack
        self._update_system_state(action, severity, attack_type)
        
        # Track attack duration
        if severity >= self.SEVERITY_MEDIUM:
            self.consecutive_attacks += 1
            if self.consecutive_attacks >= 3:
                self.time_under_attack = self.TIME_LONG
        else:
            self.consecutive_attacks = 0
            self.time_under_attack = self.TIME_SHORT
        
        # Advance time
        self.current_step += 1
        
        # Check terminal conditions
        if self.system_health == self.HEALTH_CRITICAL:
            # System compromised - severe penalty
            reward -= 10.0
            self.done = True
        elif self.current_step >= self.time_horizon:
            # Survived episode - bonus for healthy system
            if self.system_health == self.HEALTH_HEALTHY:
                reward += 5.0
            elif self.system_health == self.HEALTH_DEGRADED:
                reward += 2.0
            self.done = True
        
        return self._get_state(), reward, self.done
    
    def _calculate_reward(self, action: int, severity: int, attack_type: int, 
                         confidence: int) -> float:
        """
        Calculate reward for action given attack context.
        
        Reward structure exposes unsafe policies:
        - Ignoring severe attacks → negative reward
        - Overreacting to minor alerts → negative reward  
        - Appropriate responses → positive reward
        - Effective defense → damage prevention bonus
        
        Args:
            action: Chosen defense action
            severity: Attack severity level
            attack_type: Type of attack
            confidence: Alert confidence level
        
        Returns:
            Scalar reward
        """
        reward = 0.0
        
        # IGNORE action
        if action == self.IGNORE:
            if severity == self.SEVERITY_HIGH:
                # Ignoring severe attack - very bad
                reward -= 10.0
                self.damage_accumulated += 3.0
            elif severity == self.SEVERITY_MEDIUM:
                # Ignoring moderate attack - bad
                reward -= 4.0
                self.damage_accumulated += 1.0
            else:
                # Ignoring low severity - acceptable if low confidence
                if confidence == self.CONFIDENCE_LOW:
                    reward += 2.0  # Saved resources - reward conservative behavior
                else:
                    reward -= 1.0  # Missed opportunity
        
        # MONITOR action
        elif action == self.MONITOR:
            # Low cost, information gathering
            reward -= 0.2  # Small operational cost
            if severity == self.SEVERITY_LOW:
                reward += 3.0  # Great for low severity - clear signal
            elif severity == self.SEVERITY_HIGH:
                reward -= 3.0  # Insufficient for high severity
                self.damage_accumulated += 1.0
            else:
                reward += 1.0  # Reasonable for medium severity
        
        # RATE_LIMIT action
        elif action == self.RATE_LIMIT:
            reward -= 1.0  # Moderate operational cost
            if attack_type == self.TYPE_DOS or attack_type == self.TYPE_BRUTE_FORCE:
                if severity >= self.SEVERITY_MEDIUM:
                    reward += 8.0  # Very effective against these attacks - strong signal
                else:
                    reward += 3.0  # Still helpful
            else:
                reward -= 0.5  # Not very effective against scans
        
        # BLOCK_IP action
        elif action == self.BLOCK_IP:
            reward -= 1.5  # Higher operational cost (false positive risk)
            if severity == self.SEVERITY_HIGH and confidence == self.CONFIDENCE_HIGH:
                reward += 10.0  # Strong response to confirmed threat - strongest signal
            elif severity >= self.SEVERITY_MEDIUM:
                reward += 5.0  # Reasonable response
            else:
                reward -= 2.0  # Overreaction penalty
        
        # ISOLATE_SERVICE action
        elif action == self.ISOLATE_SERVICE:
            reward -= 3.0  # High operational cost (service disruption)
            if severity == self.SEVERITY_HIGH:
                if attack_type == self.TYPE_DOS:
                    reward += 12.0  # Critical defense for severe DOS - maximum reward
                else:
                    reward += 8.0  # Appropriate for severe attacks
            else:
                reward -= 4.0  # Severe overreaction penalty
        
        return reward
    
    def _update_system_state(self, action: int, severity: int, attack_type: int) -> None:
        """
        Update system health based on action effectiveness.
        
        Args:
            action: Chosen defense action
            severity: Attack severity
            attack_type: Attack type
        """
        # Determine if action was sufficient
        if severity == self.SEVERITY_HIGH:
            if action in [self.BLOCK_IP, self.ISOLATE_SERVICE]:
                # Strong action - may prevent degradation
                if self._rng.random() < 0.7:
                    return  # Successfully defended
            # Insufficient defense - health degrades
            if self.system_health == self.HEALTH_HEALTHY:
                self.system_health = self.HEALTH_DEGRADED
            elif self.system_health == self.HEALTH_DEGRADED:
                if self._rng.random() < 0.4:  # Risk of critical
                    self.system_health = self.HEALTH_CRITICAL
        
        elif severity == self.SEVERITY_MEDIUM:
            if action != self.IGNORE:
                # Some action taken
                if self.system_health == self.HEALTH_DEGRADED:
                    # May recover over time
                    if self._rng.random() < 0.3:
                        self.system_health = self.HEALTH_HEALTHY
            else:
                # Ignored - may degrade
                if self.system_health == self.HEALTH_HEALTHY:
                    if self._rng.random() < 0.2:
                        self.system_health = self.HEALTH_DEGRADED
        
        else:  # LOW severity
            # System may recover naturally
            if self.system_health == self.HEALTH_DEGRADED:
                if self._rng.random() < 0.4:
                    self.system_health = self.HEALTH_HEALTHY
    
    def _get_state(self) -> Dict:
        """
        Get current observable state.
        
        Returns:
            Dictionary containing:
            - attack_severity: Current attack severity (0-2)
            - attack_type: Type of attack (0-2)
            - system_health: System health status (0-2)
            - alert_confidence: Alert confidence level (0-1)
            - time_under_attack: Attack duration indicator (0-1)
        """
        if self.current_step < self.time_horizon:
            severity = int(self.severity_schedule[self.current_step])
            attack_type = int(self.attack_type_schedule[self.current_step])
            confidence = int(self.confidence_schedule[self.current_step])
        else:
            # Terminal state
            severity = 0
            attack_type = 0
            confidence = 0
        
        return {
            "attack_severity": severity,
            "attack_type": attack_type,
            "system_health": int(self.system_health),
            "alert_confidence": confidence,
            "time_under_attack": int(self.time_under_attack),
        }
