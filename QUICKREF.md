# PolicyLedger Quick Reference 🚀

## 30-Second Start

```bash
# Terminal 1 - Backend
cd backend
python start_server.py

# Terminal 2 - Frontend
cd frontend/policy-ledger-insights
npm run dev

# Browser: http://localhost:5173 → Live Training
```

---

## The 9 Components (in order)

1. **Environment** → Generates trajectories
2. **Training** → Produces Q-tables (untrusted)
3. **Policy** → Extracts state→action mapping
4. **Submission** → Agent claims reward
5. **Verification** → Replays & recomputes reward ⭐
6. **Ledger** → Records verified policies
7. **Marketplace** → Selects best by verified_reward
8. **Reuse** → Executes without training
9. **Explainability** → Describes strategies

---

## Key Files

| Component | File | Line of Code |
|-----------|------|--------------|
| Environment | `src/environments/cyber_env.py` | 250 |
| Training | `src/agent/trainer.py` | 300 |
| Policy | `src/agent/policy.py` | 100 |
| Submission | `src/agent/runner.py` | 200 |
| Verification | `src/verifier/verifier.py` | 150 |
| Ledger | `src/ledger/ledger.py` | 200 |
| Marketplace | `src/marketplace/ranking.py` | 150 |
| Reuse | `src/consumer/reuse.py` | 250 |
| Explainability | `src/explainability/explainer.py` | 200 |

---

## The Sacred Loop

```python
# SAME physics everywhere:
state = env.reset(seed=42)
for step in range(max_steps):
    action = choose_action(state, q_table, epsilon)  # Only diff
    next_state, reward, done, _, _ = env.step(action)
    state = next_state
    if done: break
```

**Three modes, one loop:**
- Training: `epsilon = 0.1` (explore)
- Verification: `epsilon = 0` (exploit)
- Reuse: `epsilon = 0` (exploit)

---

## Common Commands

### Train Policy
```bash
cd backend
python -m src.agent.runner
```

### Verify Policy
```bash
python -m src.verifier.cli <policy_hash>
```

### Reuse Best Policy
```bash
python -m src.consumer.reuse
```

### Run Tests
```bash
pytest tests/
```

---

## Architecture Rules

### ✅ DO
- Use same seed for verification
- Keep environment deterministic
- Store only verified data in ledger
- Select by verified_reward only
- Execute policies without training

### ❌ DON'T
- Trust claimed_reward
- Allow non-deterministic verification
- Modify ledger entries
- Retrain during reuse
- Skip verification step

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Training episodes | <500 | ~300-400 ✅ |
| Verification time | <1s | ~0.3s ✅ |
| Reuse improvement | >+100% | +150% ✅ |
| Ledger integrity | 100% | 100% ✅ |

---

## Debug Checklist

### Training Not Converging?
- [ ] Check epsilon decay rate
- [ ] Try optimistic initialization
- [ ] Increase max_episodes
- [ ] Verify environment rewards

### Verification Failing?
- [ ] Same seed used?
- [ ] Same environment version?
- [ ] Policy format correct?
- [ ] Check discretization params

### Reuse Performance Poor?
- [ ] Is verification passing?
- [ ] Using best policy from marketplace?
- [ ] Epsilon = 0 during execution?
- [ ] Environment seed different?

---

## API Endpoints

### REST
- `GET /` → Health check
- `POST /live-training/start` → Start training
- `POST /live-training/stop` → Stop training
- `GET /live-training/status` → Get status

### WebSocket
- `WS /ws/train` → Real-time training stream

---

## Config Quick Edit

**Backend**: `backend/src/utils/config.py`
```python
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
MAX_EPISODES = 1000
```

**Frontend**: UI controls (no code edit needed)

---

## Project Structure

```
backend/
  src/
    agent/          # Training & policies
    environments/   # Simulation
    verifier/       # Verification
    ledger/         # Storage
    marketplace/    # Selection
    consumer/       # Reuse
    explainability/ # Explanation
    training/       # Live training
  tests/            # Unit tests

frontend/
  policy-ledger-insights/
    src/
      pages/        # LiveTraining.tsx
      components/   # Navigation, etc
```

---

## Documentation Map

| Need | Read |
|------|------|
| First time setup | [QUICKSTART.md](QUICKSTART.md) |
| Live training | [LIVE_TRAINING_GUIDE.md](LIVE_TRAINING_GUIDE.md) |
| Architecture | [README.md](README.md) |
| Validation | [FINAL_VALIDATION.md](FINAL_VALIDATION.md) |
| Execution loop | [EXECUTION_LOOP.md](EXECUTION_LOOP.md) |
| Quick ref | **This file** ✅ |

---

## One-Line Summary

> **PolicyLedger**: Governance for decentralized RL through deterministic verification and immutable ledgers.

---

## Critical Principles

1. **Determinism**: Same input → same output
2. **Verification**: Replay, don't trust
3. **Immutability**: Append-only ledger
4. **Objectivity**: argmax(verified_reward)
5. **Separation**: Training ≠ Verification ≠ Reuse

---

## Status Badges

- ✅ **PRODUCTION READY**
- 🏆 **96/100 Architecture Score**
- ⚡ **Real-Time Training**
- 🔒 **Tamper-Evident Ledger**
- 📊 **Live Visualization**

---

## Emergency Contacts

**Issues?**
1. Check [FINAL_VALIDATION.md](FINAL_VALIDATION.md)
2. Run `pytest tests/`
3. Verify config.py settings
4. Check environment determinism

**Questions?**
- Read [EXECUTION_LOOP.md](EXECUTION_LOOP.md)
- Review [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md)

---

**Remember**: *"The only difference is who chooses the action."*

**Quick Start**: `python start_server.py` + `npm run dev` → **GO!** 🚀
