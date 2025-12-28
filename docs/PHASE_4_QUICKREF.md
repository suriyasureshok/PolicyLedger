# 🚀 Phase 4 Quick Reference

## One-Line Summary
**Train a local RL agent → Get verifiable policy claim**

---

## 🎯 Quick Start

```python
from src.agent import quick_train

# Train agent (simplest way)
claim = quick_train(agent_id="agent_001", seed=42, episodes=500)

# View results
print(claim.claimed_reward)  # Performance claim
print(claim.policy_hash)     # Verifiable fingerprint
```

---

## 📋 Common Tasks

### Task 1: Train Single Agent
```python
from src.agent import run_agent

claim = run_agent(
    agent_id="agent_001",
    seed=42,
    episodes=1000
)
```

### Task 2: Train Multiple Agents (Decentralized)
```python
agents = []
for i in range(10):
    claim = run_agent(
        agent_id=f"agent_{i:03d}",
        seed=42 + i * 10,  # Different env per agent
        episodes=1000
    )
    agents.append(claim)
```

### Task 3: Inspect Learned Policy
```python
from src.agent.policy import deserialize_policy

policy = deserialize_policy(claim.policy_artifact)
print(f"Policy has {len(policy)} state→action mappings")

# View specific decision
state = (0, 5, 1)  # (time_bucket, battery_bucket, demand)
action = policy.get(state, None)
print(f"Action: {'USE' if action == 1 else 'SAVE'}")
```

### Task 4: Verify Policy Hash
```python
from src.agent.policy import hash_policy

# Recompute hash
recomputed = hash_policy(claim.policy_artifact)
assert recomputed == claim.policy_hash  # Should match
```

### Task 5: Custom Environment
```python
claim = run_agent(
    agent_id="agent_custom",
    seed=123,
    episodes=2000,
    time_slots=48,           # Longer horizon
    battery_capacity=2.0,    # Bigger battery
    energy_cost=0.05         # Lower cost
)
```

---

## 🔧 Module Functions

### State Handling (`state.py`)
```python
from src.agent import discretize_state

# Convert raw state to discrete tuple
discrete_state = discretize_state({
    "time_slot": 10,
    "battery_level": 0.75,
    "demand": 1
})
# Returns: (time_bucket, battery_bucket, demand)
```

### Training (`trainer.py`)
```python
from src.agent import train
from src.shared.env import EnergySlotEnv

env = EnergySlotEnv(seed=42)
q_table, avg_reward = train(env, episodes=1000)
```

### Policy Extraction (`policy.py`)
```python
from src.agent import extract_policy, serialize_policy, hash_policy

# Extract deterministic policy
policy = extract_policy(q_table)

# Serialize for storage
policy_bytes = serialize_policy(policy)

# Generate hash
policy_hash = hash_policy(policy_bytes)
```

---

## 📊 PolicyClaim Object

```python
class PolicyClaim:
    agent_id: str           # "agent_001"
    env_id: str            # "energy_slot_env_seed_42_slots_24"
    policy_hash: str       # "85270f7725cd47d9..."
    policy_artifact: bytes # Serialized policy
    claimed_reward: float  # 7.606
```

---

## ⚙️ Configuration (`src/shared/config.py`)

### Hyperparameters (DO NOT MODIFY DURING TRAINING)
```python
ALPHA = 0.1              # Learning rate
GAMMA = 0.95             # Discount factor
EPSILON_START = 1.0      # Initial exploration
EPSILON_END = 0.01       # Min exploration
EPSILON_DECAY = 0.995    # Decay per episode
```

### Discretization
```python
BATTERY_BUCKETS = 10     # Battery discretization
TIME_SLOT_BUCKETS = 6    # Time discretization
```

### Training Defaults
```python
DEFAULT_EPISODES = 1000
DEFAULT_TIME_SLOTS = 24
DEFAULT_BATTERY_CAPACITY = 1.0
DEFAULT_ENERGY_COST = 0.1
```

---

## 🎮 Action Space

```python
ACTION_SAVE = 0  # Don't use energy
ACTION_USE = 1   # Use energy
```

---

## 🧪 Testing

### Run Tests
```bash
python test_agent.py
```

### Run Examples
```bash
python examples_phase4.py
```

---

## 📈 Typical Performance

- **Training Speed**: ~500 episodes in <1 second
- **Policy Size**: ~80 state→action mappings
- **Artifact Size**: ~2-5 KB
- **Claimed Reward**: ~5-8 (depends on seed & training)

---

## 🚫 What Agent Does NOT Do

- ❌ Verify its own claims
- ❌ Access blockchain/ledger
- ❌ See other agents
- ❌ Rank policies
- ❌ Self-compare

**Separation of concerns**: Agent learns, Verifier judges, Ledger records.

---

## 🔗 Integration Points

### Input (from Environment)
```python
from src.shared.env import EnergySlotEnv
env = EnergySlotEnv(seed=42)
```

### Output (to Verifier - Phase 5)
```python
claim = run_agent(...)
# Pass claim to verifier for validation
```

---

## 💡 Best Practices

1. **Use unique agent IDs**: `agent_001`, `agent_002`, etc.
2. **Use different seeds for different environments**: `seed=42+i*10`
3. **Train enough episodes**: Minimum 500, recommended 1000+
4. **Keep hyperparameters fixed**: Don't tune during training
5. **Store claims properly**: Save `policy_artifact` and `policy_hash`

---

## 🐛 Common Issues

### Issue: Low Reward
- **Solution**: Train more episodes or adjust hyperparameters in config

### Issue: Same Policies
- **Solution**: Use different seeds for different environments

### Issue: Slow Training
- **Solution**: Reduce episodes or use smaller state space

---

## 📚 File Structure Reference

```
src/agent/
├── __init__.py   → Exports all public functions
├── state.py      → discretize_state()
├── trainer.py    → train(), select_action(), etc.
├── policy.py     → extract_policy(), serialize_policy(), hash_policy()
└── runner.py     → run_agent(), quick_train()
```

---

## 🔍 Debugging

### Print Q-table Size
```python
q_table, _ = train(env, episodes=500)
print(f"Q-table has {len(q_table)} entries")
```

### View Policy Decisions
```python
policy = extract_policy(q_table)
for state, action in list(policy.items())[:10]:
    print(f"State {state} → Action {'USE' if action else 'SAVE'}")
```

### Check Determinism
```python
claim1 = quick_train("a1", seed=42, episodes=500)
claim2 = quick_train("a2", seed=42, episodes=500)
assert claim1.policy_hash == claim2.policy_hash  # Should match
```

---

## ✅ Checklist for Implementation

- [x] State discretization implemented
- [x] Q-learning trainer implemented
- [x] Policy extraction implemented
- [x] Serialization implemented
- [x] Hashing implemented
- [x] Runner orchestration implemented
- [x] PolicyClaim dataclass defined
- [x] Tests passing
- [x] Examples working
- [x] Documentation complete

---

## 🎯 Next Phase

After completing Phase 4, move to:
- **Phase 5**: Verifier (validates policy claims)
- **Phase 6**: Ledger (stores verified policies)
- **Phase 7**: Marketplace (ranks & trades policies)

---

**Need help? Check**: `PHASE_4_COMPLETE.md` for full documentation
