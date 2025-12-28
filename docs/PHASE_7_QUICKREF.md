# 🔥 PHASE 7 QUICKREF — VERIFICATION LAYER

## Core Principle
> **"Trust is derived from replayability, not reputation."**

## Quick Usage

### Verify a claim:
```python
from src.verifier import verify_claim, VerificationStatus

# Verify any PolicyClaim
result = verify_claim(claim, reward_threshold=1e-6)

# Check result
if result.status == VerificationStatus.VALID:
    print(f"✅ Verified: {result.verified_reward}")
else:
    print(f"❌ Rejected: {result.reason}")
```

### Use verifier class:
```python
from src.verifier import PolicyVerifier

verifier = PolicyVerifier(reward_threshold=1e-6)
result = verifier.verify(claim)
```

## Key Components

### 1. Policy Loader
**What:** Deserializes and validates policy artifacts  
**Rejects:** Empty policies, invalid structures, incomplete mappings

### 2. Replay Engine  
**What:** Re-runs environment with policy deterministically  
**Rules:** Same seed, no exploration, no randomness  
**Critical:** Uses exact same `discretize_state()` as training

### 3. Reward Comparator
**What:** Compares claimed vs verified rewards  
**Decision:** `|claimed - verified| <= threshold`  
**Threshold:** `1e-6` (floating-point safety)

## Edge Cases Handled

| Case | Detection | Result |
|------|-----------|--------|
| Inflated reward | Replay mismatch | INVALID |
| Hash mismatch | SHA-256 check | INVALID |
| Incomplete policy | Missing state-action | INVALID |
| Non-determinism | Multiple replays differ | SYSTEM ERROR |

## Test Commands

```bash
# Run all verification tests
python -m pytest tests/test_verification.py -v

# Run integration test
python -m pytest tests/test_integration.py -v

# Run demo
python demo_verification.py
```

## Files

```
src/verifier/
  ├── __init__.py          # Public API
  └── verifier.py          # Core implementation (454 lines)

tests/
  ├── test_verification.py # 10 tests, all passing
  └── test_integration.py  # End-to-end workflow

demo_verification.py       # 6 demonstrations
```

## API Reference

### VerificationResult
```python
VerificationResult(
    agent_id: str,
    policy_hash: str,
    verified_reward: Optional[float],
    status: VerificationStatus,  # VALID | INVALID
    reason: str
)
```

### PolicyVerifier
```python
verifier = PolicyVerifier(reward_threshold=1e-6)
result = verifier.verify(claim)  # → VerificationResult
is_det = verifier.verify_determinism(claim, num_runs=3)  # → bool
```

## Verification Flow

```
PolicyClaim
    ↓
[1] Validate hash (SHA-256)
    ↓
[2] Load policy artifact
    ↓
[3] Replay in environment
    ↓
[4] Compare rewards
    ↓
VerificationResult (VALID | INVALID)
```

## What Verifier NEVER Does

❌ Rank policies  
❌ Write to ledger  
❌ Retry claims  
❌ Ask for clarification  
❌ Store history  
❌ Adjust thresholds dynamically

**Verifier = judge, not coach**

## Judge Talking Points

**Q: What's novel?**  
A: "We verify through deterministic replay, not reputation."

**Q: How prevent cheating?**  
A: "Hash verification + deterministic replay catches all tampering."

**Q: Why not blockchain?**  
A: "Verification is deterministic - no need for consensus."

## Exit Criteria (ALL MET ✅)

- ✅ Valid claims pass
- ✅ Inflated rewards rejected
- ✅ Hash mismatches detected
- ✅ Deterministic replay confirmed
- ✅ Binary & explainable decisions

## Next Steps

**Phase 8:** Ledger (immutable storage)  
**Phase 9:** Marketplace (ranking)  
**Phase 10:** Policy Reuse (wow moment)

---

**Status:** ✅ COMPLETE  
**Ready for:** Phase 8
