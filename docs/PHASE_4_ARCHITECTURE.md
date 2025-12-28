# 🏗️ Phase 4 Architecture Diagram

## 📐 Component Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        RL AGENT MODULE                          │
│                   (Edge Learning Node)                          │
└─────────────────────────────────────────────────────────────────┘

                             ┌──────────┐
                             │ runner.py│
                             │  (Glue)  │
                             └────┬─────┘
                                  │
                    run_agent(agent_id, seed, episodes)
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
    │  state.py     │    │ trainer.py    │    │  policy.py    │
    │               │    │               │    │               │
    │ discretize    │◄───│  Q-learning   │───►│  extract      │
    │   state       │    │   algorithm   │    │  serialize    │
    └───────────────┘    └───────┬───────┘    │  hash         │
                                 │            └───────────────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ EnergySlotEnv │
                         │  (from Phase 3)│
                         └───────────────┘
```

## 🔄 Training Loop (Detailed)

```
┌─────────────────────────────────────────────────────────────────┐
│                      TRAINING EPISODE                           │
└─────────────────────────────────────────────────────────────────┘

1. ENVIRONMENT RESET
   ┌──────────────┐
   │ env.reset()  │ → {time_slot: 0, battery: 1.0, demand: 1}
   └──────┬───────┘
          │
          ▼
2. DISCRETIZE STATE
   ┌────────────────────┐
   │ discretize_state() │ → (time_bucket, battery_bucket, demand)
   └─────────┬──────────┘
             │
             ▼
3. SELECT ACTION (ε-greedy)
   ┌─────────────────┐
   │ select_action() │ → 0 (SAVE) or 1 (USE)
   └────────┬────────┘
            │
            ▼
4. TAKE ACTION
   ┌────────────────┐
   │ env.step(act)  │ → (next_state, reward, done)
   └────────┬───────┘
            │
            ▼
5. UPDATE Q-TABLE
   ┌──────────────────┐
   │ update_q_value() │ Q(s,a) ← Q(s,a) + α[r + γ·maxQ(s',a') - Q(s,a)]
   └────────┬─────────┘
            │
            ▼
6. REPEAT until done
   │
   ▼
7. RETURN total_reward
```

## 🎯 Data Flow

```
INPUT                   PROCESSING                   OUTPUT
─────                   ──────────                   ──────

Raw Environment     →   State Module      →   Discrete State
{time, battery,         discretize_state()    (0, 7, 1)
 demand}

Discrete State     →   Trainer Module     →   Action
(0, 7, 1)              select_action()        0 or 1
                       + Q-table

Action + Env       →   Environment        →   Reward + Next State
0 or 1                 env.step()             -1.0, (0, 7, 0)

Experience         →   Trainer Module     →   Updated Q-table
(s,a,r,s')            update_q_value()       {(s,a): q_val}

Q-table            →   Policy Module      →   Deterministic Policy
{(s,a): q_val}        extract_policy()       {s: best_a}

Policy             →   Policy Module      →   Serialized Bytes
{s: a}                serialize_policy()     b'{...}'

Policy Bytes       →   Policy Module      →   SHA-256 Hash
b'{...}'              hash_policy()          "85270f77..."

All Artifacts      →   Runner Module      →   PolicyClaim
                      run_agent()            (agent_id, hash, reward)
```

## 🧩 Module Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                         state.py                                │
│  Responsibility: Interpret the world                            │
│  Input:  Raw environment state                                  │
│  Output: Discrete state tuple                                   │
│  Does:   Bucketing, discretization                              │
│  DOES NOT: Modify env, access Q-table, use randomness          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        trainer.py                               │
│  Responsibility: Learn from experience                          │
│  Input:  Environment, hyperparameters                           │
│  Output: Trained Q-table, average reward                        │
│  Does:   Q-learning, exploration, exploitation                  │
│  DOES NOT: Serialize, verify, store to ledger                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         policy.py                               │
│  Responsibility: Transform knowledge into shareable artifact    │
│  Input:  Q-table                                                │
│  Output: Policy bytes, hash                                     │
│  Does:   Extract best actions, serialize, hash                  │
│  DOES NOT: Train, modify environment, verify                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         runner.py                               │
│  Responsibility: Orchestrate workflow                           │
│  Input:  Agent ID, seed, parameters                             │
│  Output: PolicyClaim                                            │
│  Does:   Coordinate all modules                                 │
│  DOES NOT: Contain business logic, verify, store               │
└─────────────────────────────────────────────────────────────────┘
```

## 🔐 Decentralization Model

```
                    NO COMMUNICATION
                    
Agent 1             Agent 2             Agent 3
┌─────────┐        ┌─────────┐        ┌─────────┐
│ seed=42 │        │ seed=52 │        │ seed=62 │
│ Train   │        │ Train   │        │ Train   │
│ ↓       │        │ ↓       │        │ ↓       │
│ Claim 1 │        │ Claim 2 │        │ Claim 3 │
└────┬────┘        └────┬────┘        └────┬────┘
     │                  │                  │
     └──────────────────┼──────────────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  VERIFIER       │
               │  (Phase 5)      │
               │  Validates all  │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  LEDGER         │
               │  (Phase 6)      │
               │  Stores verified│
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │  MARKETPLACE    │
               │  (Phase 7)      │
               │  Ranks & trades │
               └─────────────────┘

KEY PRINCIPLE: Agents never see each other during training
```

## 🎓 Q-Learning Update Rule (Visual)

```
Current Q-value              Best future Q-value
     ↓                              ↓
Q(s,a) ← Q(s,a) + α · [r + γ · max Q(s',a') - Q(s,a)]
                      ↑         ↑               ↑
                   Learning  Discount      Prediction
                    rate      factor         error

Where:
  s   = current state
  a   = action taken
  r   = reward received
  s'  = next state
  α   = learning rate (0.1)
  γ   = discount factor (0.95)
```

## 🏭 Policy Claim Structure

```
PolicyClaim
├── agent_id: "agent_001"
│   └── Unique identifier for this agent
│
├── env_id: "energy_slot_env_seed_42_slots_24"
│   └── Identifies environment configuration
│
├── policy_hash: "85270f7725cd47d9c2ba02f840dbb3d4..."
│   └── SHA-256 fingerprint (64 hex chars)
│
├── policy_artifact: b'{"(0,7,1)":1,"(0,8,0)":0,...}'
│   └── Serialized policy (JSON bytes)
│
└── claimed_reward: 7.606
    └── Agent's performance claim
```

## 🔄 State Space Visualization

```
Original State (Continuous)
┌──────────────────────────┐
│ time_slot: 0-23          │
│ battery_level: 0.0-1.0   │
│ demand: 0 or 1           │
└──────────────────────────┘
            │
            │ discretize_state()
            ▼
Discrete State (Bucketed)
┌──────────────────────────┐
│ time_bucket: 0-5         │  ← 24 slots → 6 buckets
│ battery_bucket: 0-9      │  ← 0.0-1.0 → 10 buckets
│ demand: 0 or 1           │  ← Already discrete
└──────────────────────────┘
            │
            │ Used as Q-table key
            ▼
Q-table Entry
┌──────────────────────────┐
│ ((0,7,1), 0): -0.5      │  ← State + SAVE action
│ ((0,7,1), 1):  1.2      │  ← State + USE action
└──────────────────────────┘
            │
            │ extract_policy()
            ▼
Policy Entry
┌──────────────────────────┐
│ (0,7,1): 1              │  ← Best action (USE)
└──────────────────────────┘
```

## 📊 Typical Training Progression

```
Episode 1-100: Exploration Phase (ε ≈ 1.0 → 0.6)
──────────────────────────────────────────────────
Reward: -5 to +3 (random exploration)
Q-table: Growing rapidly
Policy: Unstable

Episode 100-500: Learning Phase (ε ≈ 0.6 → 0.2)
──────────────────────────────────────────────────
Reward: +3 to +6 (patterns emerging)
Q-table: Most states visited
Policy: Converging

Episode 500-1000: Refinement Phase (ε ≈ 0.2 → 0.01)
──────────────────────────────────────────────────
Reward: +6 to +8 (exploitation)
Q-table: Stable values
Policy: Near-optimal

Final Policy: Deterministic, stable
```

## 🛡️ Verification Points

```
Agent Output          Verification          Next Stage
─────────────         ────────────          ──────────

PolicyClaim      →   Verifier (Phase 5)
                     • Re-run policy
                     • Check hash
                     • Validate reward
                                      →   Verified Claim

Verified Claim   →   Ledger (Phase 6)
                     • Store on blockchain
                     • Timestamp
                     • Link to agent
                                      →   Ledger Entry

Ledger Entry     →   Marketplace (Phase 7)
                     • Rank policies
                     • Enable trading
                     • Show leaderboard
                                      →   Public Policy
```

---

**🎯 Key Takeaway**: Clean separation at every layer. Agent learns, produces claim, and stops. No verification, no storage, no comparison. That's the next phase's job.

