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


def initialize_q_table(optimistic_value: float = 0.0) -> Dict[Tuple[Tuple[int, int, int], int], float]:
    """
    Create an empty Q-table with optional optimistic initialization.

    Structure: {(state, action): q_value}
    where state is a tuple (time_bucket, battery_bucket, demand)

    Args:
        optimistic_value: Initial Q-value for unseen state-action pairs.
                         Use 0.0 for neutral initialization,
                         positive values for optimistic exploration.

    Returns:
        Empty dictionary that will be populated during training.

    Rules:
        - Does NOT assume fixed state space
        - Does NOT pre-fill everything
        - Lazy initialization: states added as encountered
        - Memory efficient for large state spaces
        - Optimistic init encourages exploration of unseen states
    """
    return {}


def select_action(
    state: Tuple[int, int, int],
    q_table: Dict,
    epsilon: float,
    optimistic_value: float = 0.0
) -> int:
    """
    Select action using epsilon-greedy strategy with optimistic initialization.

    This is the explore vs exploit decision that balances learning
    and exploitation of known good actions.

    Args:
        state: Discrete state tuple (time_bucket, battery_bucket, demand)
        q_table: Current Q-table mapping (state, action) to Q-values
        epsilon: Current exploration rate (0.0 to 1.0)
        optimistic_value: Default Q-value for unseen state-action pairs

    Returns:
        Selected action (0=SAVE or 1=USE)

    Rules:
        - Does NOT update Q-values
        - Does NOT look ahead
        - Simple epsilon-greedy with random tie-breaking
        - Exploration probability decreases over training
        - Optimistic values encourage exploration
    """
    # Exploration: random action
    if random.random() < epsilon:
        return random.choice(ACTIONS)
    
    # Exploitation: best known action
    # Get Q-values for all actions in this state (optimistic for unseen)
    q_values = [q_table.get((state, action), optimistic_value) for action in ACTIONS]
    
    # Choose action with highest Q-value (ties broken randomly)
    max_q = max(q_values)
    best_actions = [action for action in ACTIONS if q_table.get((state, action), optimistic_value) == max_q]
    
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


def train_episode(env, q_table: Dict, epsilon: float, discretize_fn=None, 
                 q_table_a: Dict = None, q_table_b: Dict = None, 
                 replay_buffer=None) -> Tuple[float, Dict[str, int]]:
    """
    Run one full training episode with Double Q-Learning and Experience Replay.

    This is one practice exam where the agent learns from experience
    by interacting with the environment and updating its Q-values using
    an advanced Double Q-Learning algorithm with replay buffer.

    Args:
        env: Environment instance with reset() and step() methods
        q_table: Main Q-table (used for backward compatibility)
        epsilon: Current exploration rate for action selection
        discretize_fn: Optional state discretization function (defaults to discretize_state)
        q_table_a: First Q-table for Double Q-Learning (if None, uses standard Q-learning)
        q_table_b: Second Q-table for Double Q-Learning (if None, uses standard Q-learning)
        replay_buffer: ExperienceReplay buffer for batch learning (if None, uses online learning)

    Returns:
        Tuple of (total_reward, action_counts)
        - total_reward: Total reward accumulated in this episode
        - action_counts: Dictionary mapping action names to counts

    Rules:
        - Does NOT reset env multiple times
        - Does NOT aggregate across episodes
        - Single episode: reset → loop → done
        - Updates Q-tables in-place during episode
        - If replay_buffer provided, stores experiences and performs batch updates
    """
    if discretize_fn is None:
        discretize_fn = discretize_state
    
    # Determine if using Double Q-Learning
    use_double_q = (q_table_a is not None and q_table_b is not None)
    
    # Reset environment
    env_state = env.reset()
    state = discretize_fn(env_state)
    
    total_reward = 0.0
    done = False
    action_counts = {}
    
    # Run episode until termination
    while not done:
        # Select action using appropriate method
        if use_double_q:
            from ..agent.double_q_learning import select_action_double_q
            action = select_action_double_q(state, q_table_a, q_table_b, epsilon)
        else:
            action = select_action(state, q_table, epsilon, optimistic_value=0.0)
        
        # Track actions
        action_name = str(action)
        action_counts[action_name] = action_counts.get(action_name, 0) + 1
        
        # Take action in environment
        next_env_state, reward, done = env.step(action)
        next_state = discretize_fn(next_env_state)
        
        # Store experience in replay buffer if provided
        if replay_buffer is not None:
            replay_buffer.add(state, action, reward, next_state, done)
        
        # Update Q-table(s)
        if use_double_q:
            from ..agent.double_q_learning import update_double_q_tables
            update_double_q_tables(q_table_a, q_table_b, state, action, reward, next_state, done)
        else:
            update_q_value(q_table, state, action, reward, next_state, done)
        
        # Accumulate reward
        total_reward += reward
        
        # Move to next state
        state = next_state
    
    # Perform replay learning if buffer has enough experiences
    if replay_buffer is not None and replay_buffer.can_sample():
        from ..agent.double_q_learning import update_double_q_tables
        batch = replay_buffer.sample()
        for exp_state, exp_action, exp_reward, exp_next_state, exp_done in batch:
            if use_double_q:
                update_double_q_tables(q_table_a, q_table_b, exp_state, exp_action, 
                                     exp_reward, exp_next_state, exp_done)
            else:
                update_q_value(q_table, exp_state, exp_action, exp_reward, exp_next_state, exp_done)
    
    return total_reward, action_counts


def train(env, episodes: int, convergence_window: int = 100, convergence_threshold: float = 0.01) -> Tuple[Dict, float, Dict]:
    """
    Train agent for specified number of episodes with convergence detection.
    
    This is the full study session where the agent learns an optimal
    policy through repeated interaction with the environment.
    
    Args:
        env: Environment instance for training
        episodes: Maximum number of episodes to train
        convergence_window: Window size for checking convergence
        convergence_threshold: Max reward stddev for convergence
    
    Returns:
        Tuple of (trained_q_table, average_reward, training_stats) where:
        - trained_q_table: Complete Q-table after training
        - average_reward: Mean reward across all training episodes
        - training_stats: Dictionary with training metrics
            - converged: Whether training converged early
            - episodes_trained: Actual episodes completed
            - final_epsilon: Final exploration rate
            - q_table_size: Number of state-action pairs learned
            - reward_history: List of episode rewards
    
    Rules:
        - Does NOT serialize policy
        - Does NOT submit results
        - Just trains and returns artifacts
        - Uses exponential epsilon decay for exploration
        - Can converge early if reward stabilizes
    """
    q_table = initialize_q_table()
    epsilon = EPSILON_START
    
    episode_rewards = []
    converged = False
    episodes_trained = 0
    
    for episode in range(episodes):
        # Train one episode
        reward, _ = train_episode(env, q_table, epsilon)
        episode_rewards.append(reward)
        episodes_trained = episode + 1
        
        # Check for convergence (after sufficient episodes)
        if episode >= convergence_window:
            recent_rewards = episode_rewards[-convergence_window:]
            reward_stddev = (sum((r - sum(recent_rewards)/len(recent_rewards))**2 
                               for r in recent_rewards) / len(recent_rewards)) ** 0.5
            
            if reward_stddev < convergence_threshold:
                converged = True
                print(f"  ✓ Converged at episode {episode} (stddev: {reward_stddev:.4f})")
                break
        
        # Decay exploration rate
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)
    
    # Compute average reward
    avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0
    
    # Training statistics
    training_stats = {
        'converged': converged,
        'episodes_trained': episodes_trained,
        'final_epsilon': epsilon,
        'q_table_size': len(q_table),
        'reward_history': episode_rewards,
        'avg_reward': avg_reward,
        'final_reward': episode_rewards[-1] if episode_rewards else 0.0
    }
    
    return q_table, avg_reward, training_stats
