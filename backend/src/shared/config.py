"""
RL Agent Configuration
Fixed hyperparameters for Q-learning - DO NOT MODIFY DURING TRAINING
"""

# Q-Learning Hyperparameters
ALPHA = 0.1  # Learning rate (α)
GAMMA = 0.95  # Discount factor (γ)
EPSILON_START = 1.0  # Initial exploration rate (ε)
EPSILON_END = 0.01  # Minimum exploration rate
EPSILON_DECAY = 0.995  # Decay rate per episode

# Discretization Configuration
# State space bucketing for Q-table
BATTERY_BUCKETS = 10  # Discretize battery level into 10 buckets
TIME_SLOT_BUCKETS = 6  # Discretize time slots into 6 buckets (e.g., 24 slots → 6 groups of 4)

# Training Configuration
DEFAULT_EPISODES = 1000  # Number of training episodes
DEFAULT_TIME_SLOTS = 24  # Environment horizon
DEFAULT_BATTERY_CAPACITY = 1.0  # Battery capacity
DEFAULT_ENERGY_COST = 0.1  # Energy cost per USE action