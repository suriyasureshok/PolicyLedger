"""
Base Environment Interface

Abstract base class defining the contract for all PolicyLedger environments.
All environments must implement this interface to ensure compatibility with
the agent-verifier-ledger-marketplace pipeline.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class BaseEnv(ABC):
    """
    Abstract base class for deterministic simulation environments.
    
    All PolicyLedger environments must:
    - Be step-based (state → action → reward)
    - Be deterministic given a seed
    - Support reset() and step() operations
    - Provide observable state dictionaries
    
    This ensures verification replay produces identical results.
    """
    
    @abstractmethod
    def reset(self) -> Dict:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observable state as dictionary
        """
        pass
    
    @abstractmethod
    def step(self, action: int) -> Tuple[Dict, float, bool]:
        """
        Execute one action and advance the environment.
        
        Args:
            action: Integer action code
        
        Returns:
            Tuple of (next_state, reward, done)
            - next_state: Observable state dictionary
            - reward: Scalar reward
            - done: Boolean indicating episode termination
        """
        pass
    
    @abstractmethod
    def _get_state(self) -> Dict:
        """
        Get current observable state.
        
        Returns:
            Current state as dictionary
        """
        pass
