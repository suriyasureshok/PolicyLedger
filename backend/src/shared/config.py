"""
RL Agent Configuration for Cyber Defense Environment
Fixed hyperparameters for Q-learning - DO NOT MODIFY DURING TRAINING

TODO: Google Cloud Integration
- Vertex AI: Use for distributed agent training at scale
- Firestore: Store configuration versions for reproducibility
"""

# Q-Learning Hyperparameters
ALPHA = 0.1  # Learning rate (α)
GAMMA = 0.95  # Discount factor (γ)
EPSILON_START = 1.0  # Initial exploration rate (ε)
EPSILON_END = 0.01  # Minimum exploration rate
EPSILON_DECAY = 0.995  # Decay rate per episode

# Discretization Configuration
# State space bucketing for Q-table in cyber defense environment
ATTACK_SEVERITY_BUCKETS = 3  # LOW, MEDIUM, HIGH
ATTACK_TYPE_BUCKETS = 3  # SCAN, BRUTE_FORCE, DOS
SYSTEM_HEALTH_BUCKETS = 3  # HEALTHY, DEGRADED, CRITICAL
ALERT_CONFIDENCE_BUCKETS = 2  # LOW, HIGH
TIME_UNDER_ATTACK_BUCKETS = 2  # SHORT, LONG

# Legacy energy environment buckets (kept for backward compatibility)
BATTERY_BUCKETS = 10  # Discretize battery level into 10 buckets
TIME_SLOT_BUCKETS = 6  # Discretize time slots into 6 buckets (e.g., 24 slots → 6 groups of 4)

# Training Configuration
DEFAULT_EPISODES = 1000  # Number of training episodes
DEFAULT_TIME_HORIZON = 24  # Simulated cyber defense time horizon (decision steps)

# Legacy energy environment defaults (kept for backward compatibility)
DEFAULT_TIME_SLOTS = 24  # Environment horizon
DEFAULT_BATTERY_CAPACITY = 1.0  # Battery capacity
DEFAULT_ENERGY_COST = 0.1  # Energy cost per USE action