"""
double_q_learning.py

Improved Q-Learning with Double Q-Learning and Experience Replay

Features:
- Double Q-Learning: Reduces overestimation bias
- Experience Replay: Better sample efficiency
- Optimistic Initialization: Better exploration
- Adaptive Learning: Faster convergence
"""

from typing import Dict, Tuple, List
import random
from collections import deque
from ..shared.config import ALPHA, GAMMA, OPTIMISTIC_INIT


State = Tuple[int, int, int, int, int]
Action = int


def initialize_double_q_tables(optimistic_value: float = OPTIMISTIC_INIT) -> Tuple[Dict, Dict]:
    """Initialize two Q-tables with optimistic values for better exploration"""
    return {}, {}


def select_action_double_q(
    state: State,
    q_table_a: Dict[Tuple[State, Action], float],
    q_table_b: Dict[Tuple[State, Action], float],
    epsilon: float,
    actions: List[Action] = [0, 1, 2, 3, 4]
) -> Action:
    """
    Select action using epsilon-greedy with combined Q-tables.
    Uses average of both Q-tables for action selection.
    """
    if random.random() < epsilon:
        return random.choice(actions)
    
    # Use average of both Q-tables for action selection
    q_values = {}
    for action in actions:
        q_a = q_table_a.get((state, action), OPTIMISTIC_INIT)
        q_b = q_table_b.get((state, action), OPTIMISTIC_INIT)
        q_values[action] = (q_a + q_b) / 2
    
    return max(q_values, key=q_values.get)


def update_double_q_tables(
    q_table_a: Dict[Tuple[State, Action], float],
    q_table_b: Dict[Tuple[State, Action], float],
    state: State,
    action: Action,
    reward: float,
    next_state: State,
    done: bool,
    actions: List[Action] = [0, 1, 2, 3, 4],
    alpha: float = ALPHA,
    gamma: float = GAMMA
) -> None:
    """
    Update Q-tables using Double Q-Learning algorithm.
    Randomly choose which table to update to reduce overestimation.
    """
    # If terminal state, next_state has no value
    if done:
        gamma = 0.0
    
    if random.random() < 0.5:
        # Update Q_A using Q_B for next state value
        current_q = q_table_a.get((state, action), OPTIMISTIC_INIT)
        
        # Find best action according to Q_A
        best_next_action = max(
            actions,
            key=lambda a: q_table_a.get((next_state, a), OPTIMISTIC_INIT)
        )
        
        # Use Q_B to evaluate that action
        next_q = q_table_b.get((next_state, best_next_action), OPTIMISTIC_INIT)
        
        # Update Q_A
        new_q = current_q + alpha * (reward + gamma * next_q - current_q)
        q_table_a[(state, action)] = new_q
    else:
        # Update Q_B using Q_A for next state value
        current_q = q_table_b.get((state, action), OPTIMISTIC_INIT)
        
        # Find best action according to Q_B
        best_next_action = max(
            actions,
            key=lambda a: q_table_b.get((next_state, a), OPTIMISTIC_INIT)
        )
        
        # Use Q_A to evaluate that action
        next_q = q_table_a.get((next_state, best_next_action), OPTIMISTIC_INIT)
        
        # Update Q_B
        new_q = current_q + alpha * (reward + gamma * next_q - current_q)
        q_table_b[(state, action)] = new_q


def merge_q_tables(
    q_table_a: Dict[Tuple[State, Action], float],
    q_table_b: Dict[Tuple[State, Action], float]
) -> Dict[Tuple[State, Action], float]:
    """
    Merge two Q-tables by averaging their values.
    Used for final policy extraction.
    """
    merged = {}
    all_keys = set(q_table_a.keys()) | set(q_table_b.keys())
    
    for key in all_keys:
        q_a = q_table_a.get(key, OPTIMISTIC_INIT)
        q_b = q_table_b.get(key, OPTIMISTIC_INIT)
        merged[key] = (q_a + q_b) / 2
    
    return merged


class ExperienceReplay:
    """
    Experience Replay buffer for better sample efficiency.
    Stores (state, action, reward, next_state, done) tuples.
    """
    
    def __init__(self, max_size: int = 10000, batch_size: int = 32, min_size: int = 100):
        self.buffer = deque(maxlen=max_size)
        self.batch_size = batch_size
        self.min_size = min_size
    
    def add(self, state: State, action: Action, reward: float, next_state: State, done: bool):
        """Add experience to buffer"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int = None) -> List[Tuple[State, Action, float, State, bool]]:
        """Sample random batch from buffer"""
        batch_size = batch_size or self.batch_size
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        return random.sample(list(self.buffer), batch_size)
    
    def can_sample(self) -> bool:
        """Check if buffer has enough experiences to sample"""
        return len(self.buffer) >= self.min_size
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
