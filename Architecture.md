# PolicyLedger Architecture

**Technical Architecture & Design Documentation**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Verification Mechanism](#verification-mechanism)
5. [Security Model](#security-model)
6. [API Design](#api-design)
7. [Deployment](#deployment)

---

## System Overview

### Purpose

PolicyLedger establishes trust in untrusted distributed RL systems through deterministic verification and tamper-evident storage.

### Design Philosophy

1. **Verification over Trust**: Never trust agent claims; always verify through replay
2. **Determinism by Design**: All operations must be reproducible
3. **Immutability First**: Ledger is append-only and tamper-evident
4. **Separation of Concerns**: Clear boundaries between components
5. **Zero-Retraining Reuse**: Consumers deploy verified policies instantly

### Architecture Diagram

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

## Core Components

### 1. Environment (`src/environments/cyber_env.py`)

**Purpose**: Deterministic simulation environment for RL training and verification.

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

**Determinism Guarantees**:
- Fixed seed controls all randomness
- Step-based (not time-based) progression
- Pure functions (no side effects)
- Same seed + same actions = same trajectory

### 2. Training Agent (`src/agent/`)

**Purpose**: RL agent that learns policies through environmental interaction.

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
            verified_reward=total_reward
        )
    else:
        return VerificationResult(
            status=VerificationStatus.INVALID,
            reason=f"Reward mismatch: {reward_diff:.3f}"
        )
```

**Why Verification Works**:
- Environment is fully deterministic (seeded RNG)
- Policy is deterministic (greedy selection)
- Replay is deterministic (no exploration)
- Therefore: Same seed + same policy = same trajectory = same reward

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
│ current_hash: hash(entry_2)  │
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

**Key Differences**:
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

## Data Flow

### Complete Workflow

```
1. AGENT TRAINING
   ┌─────────────┐
   │   Agent     │
   │  (Edge)     │
   └──────┬──────┘
          │ Trains policy with Q-learning
          ▼
   ┌─────────────┐
   │   Policy    │ ← Q-table
   │  Artifact   │
   └──────┬──────┘
          │ Computes SHA-256(Q-table)
          ▼
   ┌─────────────┐
   │ Policy Claim│ ← {agent_id, policy_hash, reward}
   └──────┬──────┘
          │ Submits to API
          ▼

2. VERIFICATION
   ┌─────────────┐
   │  Verifier   │
   │ (Skeptical) │
   └──────┬──────┘
          │ Replays greedy (no exploration)
          │ Recomputes reward: 850 ✓
          ▼
   ┌─────────────┐
   │Verification │ ← {status: VALID, verified_reward}
   │   Result    │
   └──────┬──────┘
          │ Passes to ledger
          ▼

3. LEDGER RECORDING
   ┌─────────────┐
   │   Ledger    │
   └──────┬──────┘
          │ Creates hash-chained entry
          ▼
   ┌─────────────┐
   │Ledger Entry │ ← Immutable, linked to previous
   └──────┬──────┘
          │ Persists to storage
          ▼

4. MARKETPLACE RANKING
   ┌─────────────┐
   │ Marketplace │
   └──────┬──────┘
          │ Sorts by verified_reward DESC
          ▼
   ┌─────────────┐
   │Best Policy  │ ← {policy_hash, reward}
   │  Reference  │
   └──────┬──────┘
          │ Returns to consumer
          ▼

5. POLICY REUSE
   ┌─────────────┐
   │  Consumer   │
   └──────┬──────┘
          │ Executes greedy actions
          ▼
   [Deployment Complete]
```

---

## Verification Mechanism

### Deterministic Replay

**Requirements**:
1. Seeded environment
2. Deterministic policy
3. No exploration during replay

**Process**:
```python
# Same inputs
seed = 42
policy = Q_table(state -> action)

# Same execution
env1 = CyberDefenseEnv(seed=42)
env2 = CyberDefenseEnv(seed=42)

# Same outputs
reward1 = execute(policy, env1)  # 850
reward2 = execute(policy, env2)  # 850

assert reward1 == reward2  # Always true
```

### Hash Verification

**Policy Hash**:
```python
policy_hash = SHA256(json.dumps(Q_table, sort_keys=True))
```

**Chain Hash**:
```python
entry_hash = SHA256(
    policy_hash + 
    verified_reward + 
    agent_id + 
    timestamp + 
    previous_hash
)
```

---

## Security Model

### Trust Boundaries

```
+---------------------------+
|     UNTRUSTED ZONE        |
|  - Agent training         |
|  - Claimed rewards        |
+---------------------------+
            ↓
+---------------------------+
|      TRUSTED ZONE         |
|  - Verifier (replay)      |
|  - Ledger (immutable)     |
+---------------------------+
```

### Threat Model

**Protected Against**:
- ✅ False reward claims (verifier replays)
- ✅ Ledger tampering (hash chain breaks)
- ✅ Policy substitution (hash must match)

**NOT Protected Against** (out of scope):
- ❌ Sybil attacks (identity verification needed)
- ❌ DDoS attacks (network layer protection)
- ❌ Side-channel attacks (implementation level)

---

## API Design

### REST Endpoints

**Training**:
```http
POST /train
{
  "agent_id": "agent_001",
  "seed": 42,
  "episodes": 1000
}
→ 202 Accepted
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
  "verified_reward": 850.0
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
    "agent_id": "agent_001"
  }
]
```

**Marketplace**:
```http
GET /marketplace/best
→ 200 OK
{
  "policy_hash": "def456...",
  "verified_reward": 920
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
    "q_table_size": 234
  }
}
```

---

## Deployment

### Local Development (with GCP Backend)

```
┌─────────────────┐       ┌─────────────────┐
│    Frontend     │       │     Backend     │
│  (Vite dev)     │◄─────►│   (FastAPI)     │
│  localhost:5173 │  HTTP │  localhost:8000 │
└─────────────────┘  WS   └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Firestore      │
                    │ (Cloud Backend)  │
                    └──────────────────┘
```

### Production Deployment (Google Cloud)

```
┌──────────────────────────────────────────────────────┐
│                   Frontend (Hosting)                 │
│                   React SPA                          │
│            Dark Dashboard Theme                      │
│  - Deep Navy Background (#0f0c1a)                   │
│  - Purple Primary (#8b70ff)                         │
│  - Hot Pink Secondary (#ff2d75)                     │
│  - Cyan Accent (#00d4ff)                            │
│  - Glassmorphism + Neon Effects                     │
└───────────────────────┬──────────────────────────────┘
                        │ HTTPS
                        ▼
┌──────────────────────────────────────────────────────┐
│              Backend (Cloud Run)                     │
│         FastAPI + WebSocket Support                  │
└───────────┬─────────────────┬────────────────────────┘
            │                 │
            ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│    Firestore     │  │   Vertex AI      │
│  (Ledger Store)  │  │ (Verification)   │
└──────────────────┘  └──────────────────┘
```

**Frontend Architecture**:
- **Framework**: React 18 + TypeScript + Vite
- **UI Library**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS with HSL color system
- **State**: TanStack Query for server state
- **Charts**: Recharts for data visualization
- **Real-time**: WebSocket for live training updates

**Design System**:
- **Color Palette**: Dark control room theme
  - Background: HSL(250, 20%, 8%) - Almost black
  - Primary: HSL(255, 70%, 65%) - Purple
  - Secondary: HSL(330, 85%, 65%) - Hot pink
  - Accent: HSL(195, 100%, 50%) - Cyan
- **Effects**: Glassmorphism, neon glows, gradients
- **Typography**: IBM Plex Sans + IBM Plex Mono
- **Animations**: Smooth transitions, pulse effects

**Requirements** (Mandatory):
- GCP account with **billing enabled**
- gcloud CLI installed and authenticated
- Gemini API key from [makersuite.google.com](https://makersuite.google.com/app/apikey)
- Project ID

**Setup**:
```bash
.\setup-gcp.ps1  # Windows
# or
./setup-gcp.sh   # Linux/Mac
```

**Core GCP Services Used**:
- **Firestore**: Primary ledger storage (distributed NoSQL database)
- **Vertex AI**: Scalable verification compute
- **Gemini API**: AI-powered explanations and insights
- **Cloud Run**: Production API hosting with auto-scaling
- **Secret Manager**: Secure credential storage
- **Cloud Functions**: Event-driven workflows

---

## Performance Considerations

### Training Performance
- **Q-table size**: O(|S| × |A|) memory
- **Episode duration**: O(T) steps
- **Total training**: O(E × T) where E = episodes

### Verification Performance
- **Replay time**: O(T) steps (same as training episode)
- **Parallelization**: Verify multiple policies concurrently

### Ledger Performance
- **Append**: O(1) time
- **Query all**: O(N) where N = chain length
- **Integrity check**: O(N) time

---

**Document Version**: 2.0  
**Last Updated**: December 31, 2025
