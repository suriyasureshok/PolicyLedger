"""
RL Agent Configuration for Cyber Defense Environment
Fixed hyperparameters for Q-learning - DO NOT MODIFY DURING TRAINING

TODO: Google Cloud Integration
- Vertex AI: Use for distributed agent training at scale
- Firestore: Store configuration versions for reproducibility
"""

# Double Q-Learning Hyperparameters (Improved Algorithm)
ALPHA = 0.5  # Learning rate (α) - increased for faster learning
GAMMA = 0.95  # Discount factor (γ)
EPSILON_START = 1.0  # Initial exploration rate (ε)
EPSILON_END = 0.01  # Minimum exploration rate - lower for better exploitation
EPSILON_DECAY = 0.995  # Decay rate per episode

# Optimistic Initialization (for better exploration)
OPTIMISTIC_INIT = 10.0  # Initial Q-value (optimistic to encourage exploration)

# Experience Replay Configuration
REPLAY_BUFFER_SIZE = 10000  # Maximum experiences to store
REPLAY_BATCH_SIZE = 64  # Batch size for experience replay - increased
REPLAY_START_SIZE = 200  # Minimum experiences before replay starts

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
DEFAULT_EPISODES = 2000  # Number of training episodes - increased for better learning
DEFAULT_TIME_HORIZON = 24  # Simulated cyber defense time horizon (decision steps)

# Legacy energy environment defaults (kept for backward compatibility)
DEFAULT_TIME_SLOTS = 24  # Environment horizon
DEFAULT_BATTERY_CAPACITY = 1.0  # Battery capacity
DEFAULT_ENERGY_COST = 0.1  # Energy cost per USE action