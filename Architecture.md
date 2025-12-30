# PolicyLedger Architecture

**Detailed Technical Architecture & Design Documentation**

---

## 📐 Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [State Management](#state-management)
5. [Verification Mechanism](#verification-mechanism)
6. [Security Model](#security-model)
7. [API Design](#api-design)
8. [Database Schema](#database-schema)
9. [Deployment Architecture](#deployment-architecture)
10. [Performance Considerations](#performance-considerations)

---

## 🎯 System Overview

### Purpose

PolicyLedger is a **decentralized governance platform** for reinforcement learning policies. It establishes trust in untrusted distributed RL systems through deterministic verification and tamper-evident storage.

### Design Philosophy

1. **Verification over Trust**: Never trust agent claims; always verify through replay
2. **Determinism by Design**: All operations must be reproducible
3. **Immutability First**: Ledger is append-only and tamper-evident
4. **Separation of Concerns**: Clear boundaries between components
5. **Zero-Retraining Reuse**: Consumers deploy verified policies instantly

### Architecture Paradigm

```
┌─────────────────────────────────────────────────────────────┐
│                    UNTRUSTED ZONE                           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Agent 1   │  │  Agent 2   │  │  Agent N   │           │
│  │ (Training) │  │ (Training) │  │ (Training) │           │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘           │
│        │ Claims        │ Claims        │ Claims            │
└────────┼───────────────┼───────────────┼───────────────────┘
         │               │               │
         ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                     TRUSTED ZONE                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              VERIFIER (Skeptical)                    │  │
│  │  Replays policies | Recomputes rewards              │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │ Verified Results                   │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         LEDGER (Immutable, Hash-Chained)            │  │
│  │  Entry₁ → Entry₂ → Entry₃ → ... → EntryN          │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │ Verified Policies                  │
│                       ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        MARKETPLACE (Ranking & Selection)            │  │
│  │  Ranks by verified_reward | Returns best policy    │  │
│  └────────────────────┬─────────────────────────────────┘  │
└────────────────────────┼───────────────────────────────────┘
                        │ Best Policy Reference
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   CONSUMER ZONE                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           POLICY REUSE (Zero Training)              │  │
│  │  Executes best policy | No exploration              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. Environment (`src/environments/cyber_env.py`)

**Purpose**: Deterministic simulation environment for RL training and verification.

**Characteristics**:
- **Fully Deterministic**: Seeded RNG ensures reproducibility
- **Decision-Level**: Discrete state and action spaces
- **Cyber Defense Domain**: Simulates incident response decisions

**State Space** (5-tuple):
```python
State = (
    attack_severity: {LOW, MEDIUM, HIGH},
    attack_type: {SCAN, BRUTE_FORCE, DOS},
    system_health: {HEALTHY, DEGRADED, CRITICAL},
    alert_confidence: {LOW, HIGH},
    time_under_attack: {SHORT, LONG}
)
```

**Action Space** (5 actions):
```python
Actions = {
    IGNORE: 0,
    MONITOR: 1,
    RATE_LIMIT: 2,
    BLOCK_IP: 3,
    ISOLATE_SERVICE: 4
}
```

**Reward Function**:
```python
def compute_reward(state, action, next_state):
    reward = 0
    
    # Appropriate responses earn positive rewards
    if high_severity and defensive_action:
        reward += damage_prevented
    
    # Ignoring severe attacks incurs penalties
    if high_severity and action == IGNORE:
        reward -= damage_occurred
    
    # False positives and over-reactions penalized
    if low_severity and aggressive_action:
        reward -= operational_cost
    
    return reward
```

**Determinism Guarantees**:
- Fixed seed controls all randomness
- Step-based (not time-based) progression
- Pure functions (no side effects)
- Same seed + same actions = same trajectory

### 2. Training Agent (`src/agent/`)

**Purpose**: RL agent that learns policies through environmental interaction.

**Key Files**:
- `trainer.py`: Q-learning implementation
- `policy.py`: Policy representation and serialization
- `double_q_learning.py`: Advanced training with experience replay
- `runner.py`: Training orchestration and claim generation

**Training Algorithm** (Tabular Q-Learning):
```python
# Initialize Q-table
Q: Dict[State, Dict[Action, float]] = {}

# Training loop
for episode in range(num_episodes):
    state = env.reset(seed=seed)
    done = False
    
    while not done:
        # Epsilon-greedy action selection
        if random() < epsilon:
            action = random_action()  # Explore
        else:
            action = argmax(Q[state])  # Exploit
        
        # Environment step
        next_state, reward, done = env.step(action)
        
        # Q-learning update
        Q[state][action] += learning_rate * (
            reward + 
            discount * max(Q[next_state]) - 
            Q[state][action]
        )
        
        state = next_state
    
    # Decay exploration
    epsilon *= epsilon_decay
```

**Double Q-Learning Variant**:
```python
# Maintains two Q-tables to reduce overestimation bias
Q_A: Dict[State, Dict[Action, float]]
Q_B: Dict[State, Dict[Action, float]]

# Alternating updates
if random() < 0.5:
    action = argmax(Q_A[state])
    Q_A[state][action] += lr * (reward + γ * Q_B[next_state][action] - Q_A[state][action])
else:
    action = argmax(Q_B[state])
    Q_B[state][action] += lr * (reward + γ * Q_A[next_state][action] - Q_B[state][action])

# Merged policy for submission
Q_final = {s: {a: (Q_A[s][a] + Q_B[s][a]) / 2 for a in actions} for s in states}
```

**Policy Representation**:
```python
class Policy:
    def __init__(self, q_table: Dict[Tuple, Dict[int, float]]):
        self.q_table = q_table
    
    def select_action(self, state: Tuple) -> int:
        """Greedy action selection (no exploration)"""
        if state not in self.q_table:
            return default_action
        return max(self.q_table[state].items(), key=lambda x: x[1])[0]
    
    def hash(self) -> str:
        """Deterministic SHA-256 hash"""
        serialized = json.dumps(self.q_table, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
```

**Policy Claim Structure**:
```python
@dataclass
class PolicyClaim:
    agent_id: str           # Unique agent identifier
    env_id: str             # Environment configuration ID
    policy_hash: str        # SHA-256 of policy artifact
    artifact: Dict          # Q-table (state → action → value)
    claimed_reward: float   # Agent's reported performance
    seed: int               # Training seed
    env_config: Dict        # Environment parameters
```

### 3. Policy Verifier (`src/verifier/verifier.py`)

**Purpose**: Skeptical replayer that validates agent claims through deterministic execution.

**Verification Algorithm**:
```python
def verify_claim(claim: PolicyClaim) -> VerificationResult:
    # 1. Load policy artifact
    policy = deserialize_policy(claim.artifact)
    
    # 2. Create environment with same config
    env = CyberDefenseEnv(
        seed=claim.seed,
        time_horizon=claim.env_config['time_horizon']
    )
    
    # 3. Replay policy greedily (no exploration)
    total_reward = 0.0
    state = env.reset(seed=claim.seed)
    done = False
    
    while not done:
        # Greedy action selection only
        action = policy.select_action(state)
        
        # Environment step
        next_state, reward, done = env.step(action)
        total_reward += reward
        state = next_state
    
    # 4. Compare rewards
    reward_diff = abs(total_reward - claim.claimed_reward)
    
    if reward_diff <= threshold:
        return VerificationResult(
            status=VerificationStatus.VALID,
            verified_reward=total_reward,
            reason="Claim verified through deterministic replay"
        )
    else:
        return VerificationResult(
            status=VerificationStatus.INVALID,
            verified_reward=None,
            reason=f"Reward mismatch: {reward_diff:.3f}"
        )
```

**Key Properties**:
- **Deterministic**: Same input → same output
- **Skeptical**: Does not trust agent claims
- **Stateless**: Each verification is independent
- **Binary Decision**: VALID or INVALID (no partial credit)

**Why Verification Works**:
1. Environment is fully deterministic (seeded RNG)
2. Policy is deterministic (greedy selection)
3. Replay is deterministic (no exploration)
4. Therefore: Same seed + same policy = same trajectory = same reward

### 4. Tamper-Evident Ledger (`src/ledger/ledger.py`)

**Purpose**: Immutable, hash-chained storage for verified policies.

**Hash Chain Structure**:
```
Genesis Block:
┌──────────────────────────────┐
│ previous_hash: "genesis"     │
│ current_hash: hash(entry_1)  │
└──────────────────────────────┘
                │
                ▼
Entry 1:
┌──────────────────────────────┐
│ policy_hash: abc123...       │
│ verified_reward: 850         │
│ agent_id: agent_001          │
│ timestamp: 2025-12-30T...    │
│ previous_hash: genesis       │
│ current_hash: hash(entry_1)  │◄─┐
└──────────────────────────────┘  │
                │                  │
                ▼                  │ Links via hash
Entry 2:                          │
┌──────────────────────────────┐  │
│ policy_hash: def456...       │  │
│ verified_reward: 920         │  │
│ agent_id: agent_002          │  │
│ timestamp: 2025-12-30T...    │  │
│ previous_hash: entry_1.hash  │──┘
│ current_hash: hash(entry_2)  │◄─┐
└──────────────────────────────┘  │
                │                  │
                ▼                  │
Entry N:                          │
┌──────────────────────────────┐  │
│ ...                          │  │
│ previous_hash: entry_N-1.hash│──┘
│ current_hash: hash(entry_N)  │
└──────────────────────────────┘
```

**Hash Computation**:
```python
def compute_entry_hash(
    policy_hash: str,
    verified_reward: float,
    agent_id: str,
    timestamp: str,
    previous_hash: str
) -> str:
    """Deterministic hash for tamper detection"""
    data = f"{policy_hash}{verified_reward}{agent_id}{timestamp}{previous_hash}"
    return hashlib.sha256(data.encode()).hexdigest()
```

**Append Operation**:
```python
def append(self, verification_result: VerificationResult) -> LedgerEntry:
    # Get previous hash (or "genesis" if first entry)
    previous_hash = self.chain[-1].current_hash if self.chain else "genesis"
    
    # Compute current hash
    current_hash = compute_entry_hash(
        policy_hash=verification_result.policy_hash,
        verified_reward=verification_result.verified_reward,
        agent_id=verification_result.agent_id,
        timestamp=datetime.now().isoformat(),
        previous_hash=previous_hash
    )
    
    # Create immutable entry
    entry = LedgerEntry(
        policy_hash=verification_result.policy_hash,
        verified_reward=verification_result.verified_reward,
        agent_id=verification_result.agent_id,
        timestamp=datetime.now().isoformat(),
        previous_hash=previous_hash,
        current_hash=current_hash
    )
    
    # Append to chain (cannot modify existing entries)
    self.chain.append(entry)
    self.persist()
    
    return entry
```

**Integrity Verification**:
```python
def verify_chain_integrity(ledger: PolicyLedger) -> bool:
    """Detect any tampering in the chain"""
    for i, entry in enumerate(ledger.chain):
        # Recompute hash
        expected_hash = compute_entry_hash(
            entry.policy_hash,
            entry.verified_reward,
            entry.agent_id,
            entry.timestamp,
            entry.previous_hash
        )
        
        # Check hash matches
        if entry.current_hash != expected_hash:
            return False
        
        # Check previous_hash links correctly
        if i > 0 and entry.previous_hash != ledger.chain[i-1].current_hash:
            return False
    
    return True
```

**Tamper-Evidence Properties**:
- Any modification to an entry changes its hash
- This breaks the link to all subsequent entries
- Tampering is immediately detectable
- Cannot delete entries without breaking chain
- Cannot reorder entries without breaking chain

### 5. Policy Marketplace (`src/marketplace/ranking.py`)

**Purpose**: Objective policy selection based on verified performance.

**Ranking Algorithm**:
```python
def select_best_policy(ledger: PolicyLedger) -> BestPolicyReference:
    """
    Select highest-performing verified policy.
    
    Ranking criteria (in order):
    1. Highest verified_reward
    2. Most recent timestamp (tie-breaker)
    """
    if not ledger.chain:
        raise ValueError("Empty ledger")
    
    # Sort by reward (desc), then timestamp (desc)
    best_entry = max(
        ledger.chain,
        key=lambda e: (e.verified_reward, e.timestamp)
    )
    
    return BestPolicyReference(
        policy_hash=best_entry.policy_hash,
        verified_reward=best_entry.verified_reward,
        agent_id=best_entry.agent_id
    )
```

**Marketplace Invariants**:
- Only operates on verified policies
- Never modifies ledger
- Deterministic selection
- No subjective criteria
- Transparent ranking

### 6. Policy Consumer (`src/consumer/reuse.py`)

**Purpose**: Zero-retraining deployment of verified policies.

**Reuse Algorithm**:
```python
def reuse_policy(policy_ref: BestPolicyReference, env: Env) -> float:
    """
    Execute verified policy in environment.
    
    Execution rules:
    - Greedy action selection (no exploration)
    - Identical loop to training/verification
    - No learning updates
    """
    # Load policy artifact
    policy = load_policy(policy_ref.policy_hash)
    
    # Execute policy
    total_reward = 0.0
    state = env.reset()
    done = False
    
    while not done:
        # Greedy selection only
        action = policy.select_action(state)
        
        # Environment step
        next_state, reward, done = env.step(action)
        total_reward += reward
        state = next_state
    
    return total_reward
```

**Key Differences from Training**:
```
+----------------+-------------+-------------+-----------+
| Phase          | Exploration | Learning    | Q-updates |
+----------------+-------------+-------------+-----------+
| Training       | Yes (ε)     | Yes         | Yes       |
| Verification   | No (ε=0)    | No          | No        |
| Reuse          | No (ε=0)    | No          | No        |
+----------------+-------------+-------------+-----------+
```

---

## 🔄 Data Flow

### Complete Workflow

```
1. AGENT TRAINING
   ┌─────────────┐
   │   Agent     │
   │  (Edge)     │
   └──────┬──────┘
          │ Trains policy
          │ Q-learning with exploration
          │ Episodes: 1000
          ▼
   ┌─────────────┐
   │   Policy    │ ← Q-table (state→action→value)
   │  Artifact   │
   └──────┬──────┘
          │ Computes hash
          │ SHA-256(Q-table)
          ▼
   ┌─────────────┐
   │ Policy Claim│ ← {agent_id, policy_hash, reward=850}
   └──────┬──────┘
          │
          ▼ Submits to API

2. VERIFICATION
   ┌─────────────┐
   │  API Server │
   └──────┬──────┘
          │ Receives claim
          ▼
   ┌─────────────┐
   │  Verifier   │
   │ (Skeptical) │
   └──────┬──────┘
          │ Loads policy + environment
          │ Replays greedy (no exploration)
          │ Recomputes reward: 850 ✓
          ▼
   ┌─────────────┐
   │Verification │ ← {status: VALID, verified_reward: 850}
   │   Result    │
   └──────┬──────┘
          │
          ▼ Passes to ledger

3. LEDGER RECORDING
   ┌─────────────┐
   │   Ledger    │
   └──────┬──────┘
          │ Creates entry
          │ previous_hash = last_entry.hash
          │ current_hash = SHA-256(entry)
          ▼
   ┌─────────────┐
   │Ledger Entry │ ← Immutable, hash-chained
   └──────┬──────┘
          │ Persists to disk/Firestore
          ▼
   [ledger.json] or [Firestore]

4. MARKETPLACE RANKING
   ┌─────────────┐
   │ Marketplace │
   └──────┬──────┘
          │ Queries ledger
          │ Sorts by verified_reward DESC
          ▼
   ┌─────────────┐
   │Best Policy  │ ← {policy_hash: abc123, reward: 920}
   │  Reference  │
   └──────┬──────┘
          │
          ▼ Returns to consumer

5. POLICY REUSE
   ┌─────────────┐
   │  Consumer   │
   └──────┬──────┘
          │ Fetches best policy
          │ Loads artifact
          ▼
   ┌─────────────┐
   │   Policy    │
   │ Execution   │ ← Greedy actions, no learning
   └──────┬──────┘
          │
          ▼ Observes real-world reward
   [Deployment Complete]
```

---

## 💾 State Management

### Backend State

**Training Sessions** (in-memory):
```python
training_jobs: Dict[str, TrainingState] = {
    "agent_001": TrainingState(
        agent_id="agent_001",
        status="running",
        episode=450,
        total_episodes=1000,
        q_table={...},
        env=CyberDefenseEnv(...),
        metrics_history=[...]
    )
}
```

**Ledger State** (persistent):
```json
{
  "chain": [
    {
      "policy_hash": "abc123...",
      "verified_reward": 850.0,
      "agent_id": "agent_001",
      "timestamp": "2025-12-30T10:30:00",
      "previous_hash": "genesis",
      "current_hash": "def456..."
    },
    ...
  ]
}
```

**Policy Artifacts** (file system):
```
backend/policies/
├── abc123def456...policy_hash.json    # Policy 1 Q-table
├── 789ghi012jkl...policy_hash.json    # Policy 2 Q-table
└── ...
```

### Frontend State

**React Query Cache**:
```typescript
// Live training metrics
queryClient.setQueryData(['training', agentId], {
  episode: 450,
  reward: 85.3,
  avg_reward: 78.2,
  epsilon: 0.15,
  q_table_size: 234
})

// Ledger entries
queryClient.setQueryData(['ledger'], [
  { policy_hash: 'abc123...', verified_reward: 850, ... },
  ...
])

// Marketplace ranking
queryClient.setQueryData(['marketplace', 'best'], {
  policy_hash: 'abc123...',
  verified_reward: 920,
  agent_id: 'agent_002'
})
```

---

## 🔐 Security Model

### Trust Boundaries

```
+---------------------------+
|     UNTRUSTED ZONE        |
|  - Agent training         |
|  - Claimed rewards        |
|  - Edge devices           |
+---------------------------+
            ↓ Claims (untrusted)
+---------------------------+
|      TRUSTED ZONE         |
|  - Verifier (replay)      |
|  - Ledger (immutable)     |
|  - Marketplace (objective)|
+---------------------------+
```

### Threat Model

**Assumptions**:
- ✅ Agents are untrusted (can lie about rewards)
- ✅ Verifier is trusted (operates in secure environment)
- ✅ Ledger is tamper-evident (detects modifications)
- ✅ Environment is deterministic (enables verification)

**Attacks Prevented**:
1. **False Reward Claims**: Verifier replays and recomputes rewards
2. **Ledger Tampering**: Hash chain breaks if any entry modified
3. **Policy Substitution**: Policy hash must match claim
4. **Replay Attacks**: Policies stored by hash (idempotent)

**Attacks NOT Prevented** (out of scope):
1. **Model Poisoning**: Agents can submit bad policies (but verified rewards will be low)
2. **Sybil Attacks**: Single actor submitting many policies (rate limiting needed)
3. **DDoS**: Standard web security required

### Cryptographic Guarantees

**Hash Functions** (SHA-256):
- Collision resistance: ~2^128 security
- Preimage resistance: ~2^256 security
- Deterministic output

**Hash Chain Properties**:
- Forward integrity: Past cannot be changed
- Tamper evidence: Modifications detectable
- Append-only: No deletions

---

## 🌐 API Design

### REST Endpoints

**Training**:
```http
POST /train
{
  "agent_id": "agent_001",
  "seed": 42,
  "episodes": 1000,
  "config": {...}
}
→ 202 Accepted
{
  "message": "Training started",
  "agent_id": "agent_001"
}
```

**Verification**:
```http
POST /verify
{
  "agent_id": "agent_001"
}
→ 200 OK
{
  "status": "VALID",
  "verified_reward": 850.0,
  "reason": "Claim verified"
}
```

**Ledger Query**:
```http
GET /ledger
→ 200 OK
[
  {
    "policy_hash": "abc123...",
    "verified_reward": 850,
    "agent_id": "agent_001",
    "timestamp": "2025-12-30T..."
  },
  ...
]
```

**Marketplace**:
```http
GET /marketplace/best
→ 200 OK
{
  "policy_hash": "def456...",
  "verified_reward": 920,
  "agent_id": "agent_002"
}
```

### WebSocket Endpoints

**Live Training Updates**:
```javascript
ws://localhost:8000/ws/train/{agent_id}

// Server → Client messages:
{
  "type": "metrics",
  "data": {
    "episode": 450,
    "reward": 85.3,
    "avg_reward": 78.2,
    "epsilon": 0.15,
    "q_table_size": 234,
    "actions_taken": {"IGNORE": 5, "MONITOR": 12, ...}
  }
}

{
  "type": "complete",
  "data": {
    "agent_id": "agent_001",
    "final_reward": 850.0
  }
}
```

---

## 📊 Database Schema

### Local Storage (ledger.json)

```json
{
  "chain": [
    {
      "policy_hash": "string (64 chars SHA-256)",
      "verified_reward": "float",
      "agent_id": "string",
      "timestamp": "ISO 8601 string",
      "previous_hash": "string (64 chars SHA-256 or 'genesis')",
      "current_hash": "string (64 chars SHA-256)",
      "env_config": {
        "time_horizon": "int",
        "seed": "int",
        ...
      }
    }
  ]
}
```

### Firestore Schema (Google Cloud)

```
Collection: ledger_entries
├── Document: {policy_hash}
│   ├── policy_hash: string
│   ├── verified_reward: number
│   ├── agent_id: string
│   ├── timestamp: timestamp
│   ├── previous_hash: string
│   ├── current_hash: string
│   └── env_config: map

Collection: policies
├── Document: {policy_hash}
│   ├── artifact: map (Q-table)
│   ├── created_at: timestamp
│   └── metadata: map

Collection: verification_jobs
├── Document: {job_id}
│   ├── status: string
│   ├── claim: map
│   ├── result: map
│   └── created_at: timestamp
```

---

## 🚀 Deployment Architecture

### Local Development

```
┌─────────────────┐       ┌─────────────────┐
│    Frontend     │       │     Backend     │
│  (Vite dev)     │◄─────►│   (FastAPI)     │
│  localhost:5173 │  HTTP │  localhost:8000 │
└─────────────────┘  WS   └─────────────────┘
                              │
                              ▼
                         [ledger.json]
                         [policies/*.json]
```

### Google Cloud Production

```
┌──────────────────────────────────────────────────────┐
│                   Frontend (Firebase Hosting)        │
│                   https://app.policyledger.dev       │
└───────────────────────┬──────────────────────────────┘
                        │ HTTPS
                        ▼
┌──────────────────────────────────────────────────────┐
│              Backend (Cloud Run)                     │
│         FastAPI + WebSocket Support                  │
│  Auto-scaling: 1-10 instances                        │
└───────────┬─────────────────┬────────────────────────┘
            │                 │
            ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│    Firestore     │  │   Vertex AI      │
│  (Ledger Store)  │  │ (Verification)   │
│  Auto-replicated │  │ Custom Jobs      │
└──────────────────┘  └──────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────┐
│         Cloud Functions (Event-Driven)               │
│  - on_ledger_update: Update marketplace rankings     │
│  - monitor_verification: Check Vertex AI job status  │
└──────────────────────────────────────────────────────┘
```

---

## ⚡ Performance Considerations

### Training Performance

- **Q-table size**: O(|S| × |A|) memory
- **Episode duration**: O(T) steps (T = time horizon)
- **Total training**: O(E × T) where E = episodes

**Optimization**:
- Use NumPy for vectorized operations
- Sparse Q-table representation
- Early stopping when converged

### Verification Performance

- **Replay time**: O(T) steps (same as training episode)
- **Determinism overhead**: Minimal (seeded RNG)
- **Parallelization**: Verify multiple policies concurrently

**Bottleneck**: Verification is sequential per policy.

**Scalability** (Google Cloud):
- Vertex AI Custom Jobs for parallel verification
- Cloud Functions for event-driven ledger updates
- Firestore automatic scaling

### Ledger Performance

- **Append**: O(1) time
- **Query all**: O(N) where N = chain length
- **Integrity check**: O(N) time

**Optimization**:
- Cache best policy reference
- Index by verified_reward in Firestore
- Batch writes

### API Performance

- **Throughput**: ~100 req/s (local), ~1000 req/s (Cloud Run)
- **Latency**: 
  - Training submit: <50ms
  - Verification: ~1-10s (depends on episode length)
  - Ledger query: <100ms
  - Marketplace query: <50ms

**WebSocket Performance**:
- Update frequency: 10-50 updates/sec
- Concurrent connections: Limited by memory

---

## 🧪 Testing Strategy

### Unit Tests

```python
# Test deterministic environment
def test_env_determinism():
    env1 = CyberDefenseEnv(seed=42)
    env2 = CyberDefenseEnv(seed=42)
    
    for _ in range(100):
        action = random_action()
        s1, r1, d1 = env1.step(action)
        s2, r2, d2 = env2.step(action)
        
        assert s1 == s2
        assert r1 == r2
        assert d1 == d2
```

```python
# Test hash chain integrity
def test_ledger_tamper_detection():
    ledger = PolicyLedger()
    ledger.append(entry1)
    ledger.append(entry2)
    
    # Tamper with entry
    ledger.chain[0].verified_reward = 9999
    
    assert not verify_chain_integrity(ledger)
```

### Integration Tests

```python
# End-to-end workflow
def test_complete_workflow():
    # Train
    claim = train_agent(seed=42, episodes=100)
    
    # Verify
    result = verifier.verify(claim)
    assert result.status == VerificationStatus.VALID
    
    # Record
    entry = ledger.append(result)
    
    # Select
    best = marketplace.select_best_policy(ledger)
    assert best.policy_hash == claim.policy_hash
    
    # Reuse
    reward = consumer.reuse_policy(best, env)
    assert abs(reward - result.verified_reward) < threshold
```

---

## 🔮 Future Enhancements

1. **Byzantine Fault Tolerance**: Multiple verifiers with consensus
2. **Privacy-Preserving Verification**: Zero-knowledge proofs
3. **Distributed Verifier Network**: Decentralized verification
4. **Policy Compression**: Reduce storage for large policies
5. **Multi-Environment Support**: Standardized interface
6. **Adversarial Testing**: Red-team attacks on verification

---

**Document Version**: 1.0  
**Last Updated**: December 30, 2025
