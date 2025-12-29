"""
trainer.py

Q-learning training implementation for energy scheduling agent.

Detailed description:
- Implements standard Q-learning algorithm with epsilon-greedy exploration
- Trains policies for optimal energy storage decisions
- Provides complete training pipeline from initialization to convergence

Main Components:
- initialize_q_table(): Q-table creation
- select_action(): Epsilon-greedy action selection
- update_q_value(): Q-learning update rule
- train_episode(): Single episode training
- train(): Complete training pipeline

Dependencies:
- src.shared.config: Q-learning hyperparameters (ALPHA, GAMMA, EPSILON_*)
- src.agent.state: State discretization function

Author: PolicyLedger Team
Created: 2025-12-28
"""

from typing import Dict, Tuple
import random
from src.shared.config import ALPHA, GAMMA, EPSILON_START, EPSILON_END, EPSILON_DECAY
from src.agent.state import discretize_state


# Action space (fixed, explicit)
ACTION_SAVE = 0
ACTION_USE = 1
ACTIONS = [ACTION_SAVE, ACTION_USE]


def initialize_q_table() -> Dict[Tuple[Tuple[int, int, int], int], float]:
    """
    Create an empty Q-table.

    Structure: {(state, action): q_value}
    where state is a tuple (time_bucket, battery_bucket, demand)

    Returns:
        Empty dictionary that will be populated during training.

    Rules:
        - Does NOT assume fixed state space
        - Does NOT pre-fill everything
        - Lazy initialization: states added as encountered
        - Memory efficient for large state spaces
    """
    return {}


def select_action(
    state: Tuple[int, int, int],
    q_table: Dict,
    epsilon: float
) -> int:
    """
    Select action using epsilon-greedy strategy.

    This is the explore vs exploit decision that balances learning
    and exploitation of known good actions.

    Args:
        state: Discrete state tuple (time_bucket, battery_bucket, demand)
        q_table: Current Q-table mapping (state, action) to Q-values
        epsilon: Current exploration rate (0.0 to 1.0)

    Returns:
        Selected action (0=SAVE or 1=USE)

    Rules:
        - Does NOT update Q-values
        - Does NOT look ahead
        - Simple epsilon-greedy with random tie-breaking
        - Exploration probability decreases over training
    """
    # Exploration: random action
    if random.random() < epsilon:
        return random.choice(ACTIONS)
    
    # Exploitation: best known action
    # Get Q-values for all actions in this state
    q_values = [q_table.get((state, action), 0.0) for action in ACTIONS]
    
    # Choose action with highest Q-value (ties broken randomly)
    max_q = max(q_values)
    best_actions = [action for action in ACTIONS if q_table.get((state, action), 0.0) == max_q]
    
    return random.choice(best_actions)


def update_q_value(
    q_table: Dict,
    state: Tuple[int, int, int],
    action: int,
    reward: float,
    next_state: Tuple[int, int, int],
    done: bool
) -> None:
    """
    Apply Q-learning update rule.

    Q(s,a) ← Q(s,a) + α[r + γ·max_a' Q(s',a') - Q(s,a)]

    This implements the temporal difference learning update that
    propagates reward information backwards through the state space.

    Args:
        q_table: Q-table to update (modified in-place)
        state: Current state tuple
        action: Action taken in current state
        reward: Immediate reward received
        next_state: Resulting state after action
        done: Whether episode terminated (no future rewards)

    Rules:
        - Does NOT change environment
        - Does NOT store episode-level stats
        - Pure Q-learning update with standard TD(0) formula
        - Handles terminal states correctly (max_next_q = 0)
    """
    # Current Q-value (default to 0 if not seen)
    current_q = q_table.get((state, action), 0.0)
    
    # Best next Q-value (0 if terminal state)
    if done:
        max_next_q = 0.0
    else:
        next_q_values = [q_table.get((next_state, a), 0.0) for a in ACTIONS]
        max_next_q = max(next_q_values)
    
    # Q-learning update
    new_q = current_q + ALPHA * (reward + GAMMA * max_next_q - current_q)
    
    # Update table
    q_table[(state, action)] = new_q


def train_episode(env, q_table: Dict, epsilon: float) -> float:
    """
    Run one full training episode.

    This is one practice exam where the agent learns from experience
    by interacting with the environment and updating its Q-values.

    Args:
        env: Environment instance with reset() and step() methods
        q_table: Q-table to update during episode
        epsilon: Current exploration rate for action selection

    Returns:
        Total reward accumulated in this episode

    Rules:
        - Does NOT reset env multiple times
        - Does NOT aggregate across episodes
        - Single episode: reset → loop → done
        - Updates Q-table in-place during episode
    """
    # Reset environment
    env_state = env.reset()
    state = discretize_state(env_state)
    
    total_reward = 0.0
    done = False
    
    # Run episode until termination
    while not done:
        # Select action
        action = select_action(state, q_table, epsilon)
        
        # Take action in environment
        next_env_state, reward, done = env.step(action)
        next_state = discretize_state(next_env_state)
        
        # Update Q-table
        update_q_value(q_table, state, action, reward, next_state, done)
        
        # Accumulate reward
        total_reward += reward
        
        # Move to next state
        state = next_state
    
    return total_reward


def train(env, episodes: int) -> Tuple[Dict, float]:
    """
    Train agent for specified number of episodes.
    
    This is the full study session where the agent learns an optimal
    policy through repeated interaction with the environment.
    
    Args:
        env: Environment instance for training
        episodes: Number of episodes to train
    
    Returns:
        Tuple of (trained_q_table, average_reward) where:
        - trained_q_table: Complete Q-table after training
        - average_reward: Mean reward across all training episodes
    
    Rules:
        - Does NOT serialize policy
        - Does NOT submit results
        - Just trains and returns artifacts
        - Uses exponential epsilon decay for exploration
    """
    q_table = initialize_q_table()
    epsilon = EPSILON_START
    
    episode_rewards = []
    
    for episode in range(episodes):
        # Train one episode
        reward = train_episode(env, q_table, epsilon)
        episode_rewards.append(reward)
        
        # Decay exploration rate
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)
    
    # Compute average reward
    avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
    
    return q_table, avg_reward
