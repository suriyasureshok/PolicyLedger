# Running the Cyber Defense Policy Demo

## Quick Start

```bash
cd backend
python demo.py
```

## What You'll See

The demo demonstrates the complete PolicyLedger workflow with simulated cyber defense:

### 1. Agent Training (Decentralized Learning)
```
🤖 agent_alpha → Training defense policy (seed=42, episodes=150)
✅ agent_alpha → Done in 0.0s | Defense Score: -11.800
```
- 6 independent agents train cyber defense policies
- Each uses different random seed for environment diversity
- Agents learn through tabular Q-learning (150 episodes each)
- Training happens in <1 second per agent

### 2. Policy Verification (Deterministic Replay)
```
🔍 STEP 3: Verify Defense Policies via Deterministic Replay
✅ agent_epsilon → Verified Defense Score: 7.000
❌ agent_beta → Verified Defense Score: -13.900
```
- Verifier replays each policy in the same simulated environment
- Claims are accepted only if replay produces identical score
- Invalid claims (inflated scores) are REJECTED
- Verification is deterministic and reproducible

### 3. Tamper-Evident Ledger
```
📝 STEP 4: Record in Tamper-Evident Ledger
✅ agent_epsilon → Recorded (block #3)
🔗 Hash chain: ✅ INTACT
```
- Only verified policies are recorded
- Each entry is hash-chained to previous entry
- Ledger is append-only and tamper-evident
- Hash chain integrity is verified

### 4. Marketplace Ranking
```
🏆 STEP 5: Marketplace Selects Best Policy
🏆 WINNER: agent_epsilon
   Reward: 7.000
```
- Policies ranked by verified defense score
- Best policy automatically selected
- Full rankings displayed

### 5. Policy Reuse (Zero-Training Deployment)
```
🎯 STEP 6: Policy Reuse — Zero-Training Defense Deployment
✅ Policy Reuse Complete in 0.03s!
   Verified Defense Score: 7.000
   Reused Defense Score: -11.671
   Baseline (naive): -22.805
```
- Best policy deployed INSTANTLY without retraining
- Policy performance compared against naive baseline
- Demonstrates intelligent policy reuse

## Understanding the Output

### Defense Scores
- **Positive scores**: Effective defense policies that prevent damage
- **Negative scores**: Ineffective policies (ignored attacks or overreacted)
- **Score reflects**: Damage prevented minus operational costs

### Verification Status
- ✅ **VALID**: Claimed score matches verified score (within threshold)
- ❌ **INVALID**: Claimed score differs from verified score (policy rejected)

### Action Space
Agents learn to choose from:
- **IGNORE** (0): No defensive action
- **MONITOR** (1): Enhanced logging
- **RATE_LIMIT** (2): Throttle traffic
- **BLOCK_IP** (3): Block source IPs
- **ISOLATE_SERVICE** (4): Quarantine service

### State Space
Environment provides:
- **attack_severity**: LOW, MEDIUM, HIGH
- **attack_type**: SCAN, BRUTE_FORCE, DOS
- **system_health**: HEALTHY, DEGRADED, CRITICAL
- **alert_confidence**: LOW, HIGH
- **time_under_attack**: SHORT, LONG

## Key Observations

1. **Different seeds produce different policies**: Each agent learns different strategies based on the attack scenarios it encounters

2. **Verification catches inflated claims**: Agents that claim better performance than verified are rejected

3. **Policy reuse is instant**: No retraining needed, policy executes immediately

4. **Determinism is guaranteed**: Same seed + same policy = same trajectory

## Important Disclaimers

⚠️ **This is a SIMULATION**:
- Decision-level simulation for demonstrating RL verification
- NOT a real cybersecurity system
- Does NOT provide actual protection
- Used to showcase policy marketplace concept

## Files Generated

After running the demo:
- `demo_parallel_ledger.json` - Hash-chained ledger entries
- `policies/*.json` - Policy artifacts for reuse
- Console output showing complete workflow

## Architecture Demonstrated

```
Edge Agents → Train Policies → Submit Claims
                                    ↓
                              Cloud Verifier → Deterministic Replay
                                    ↓
                              Immutable Ledger → Hash-Chained Storage
                                    ↓
                              Marketplace → Rank by Performance
                                    ↓
                              Consumers → Instant Reuse
```

## Next Steps

To explore further:
1. Modify agent seeds in `demo.py` to see different learned policies
2. Check `policies/` directory to inspect learned decision rules
3. Examine `demo_parallel_ledger.json` to see hash chaining
4. Try different episode counts to see learning curves
5. Review `src/environments/cyber_env.py` for reward function details

---

**This demonstrates the core value proposition**: Learn once, verify anywhere, reuse instantly.
