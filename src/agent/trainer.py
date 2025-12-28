"""
Q-Learning Training Engine

Implements Q-learning algorithm for energy scheduling.
This is the student studying alone - no verification, no comparison.
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
    """
    return {}


def select_action(
    state: Tuple[int, int, int],
    q_table: Dict,
    epsilon: float
) -> int:
    """
    Select action using epsilon-greedy strategy.
    
    This is the explore vs exploit decision.
    
    Args:
        state: Discrete state tuple
        q_table: Current Q-table
        epsilon: Current exploration rate
    
    Returns:
        Selected action (0=SAVE or 1=USE)
    
    Rules:
        - Does NOT update Q-values
        - Does NOT look ahead
        - Simple epsilon-greedy, period
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
    
    Args:
        q_table: Q-table to update (modified in-place)
        state: Current state
        action: Action taken
        reward: Reward received
        next_state: Resulting state
        done: Whether episode terminated
    
    Rules:
        - Does NOT change environment
        - Does NOT store episode-level stats
        - Pure Q-learning update
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
    
    This is one practice exam.
    
    Args:
        env: Environment instance
        q_table: Q-table to update
        epsilon: Current exploration rate
    
    Returns:
        Total reward accumulated in this episode
    
    Rules:
        - Does NOT reset env multiple times
        - Does NOT aggregate across episodes
        - Single episode: reset → loop → done
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
    
    This is the full study session.
    
    Args:
        env: Environment instance
        episodes: Number of episodes to train
    
    Returns:
        Tuple of (trained_q_table, average_reward)
    
    Rules:
        - Does NOT serialize policy
        - Does NOT submit results
        - Just trains and returns artifacts
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
