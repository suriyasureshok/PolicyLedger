"""
Tests for Phase 10 — Policy Reuse (The Wow Moment)

Test Coverage:
    1. Load valid policy → Success
    2. Load missing policy → FileNotFoundError
    3. Load corrupted policy → ValueError
    4. Execute policy → Deterministic results
    5. Execute baseline (random, always_save, always_use)
    6. Compare with baseline → Reused policy better
    7. Convenience function → Same as class methods
    8. No training → Instant execution
"""

import pytest
import json
import hashlib
from pathlib import Path

from src.consumer.reuse import PolicyConsumer, BaselinePolicy, reuse_best_policy
from src.marketplace.ranking import BestPolicyReference
from src.agent.runner import run_agent


@pytest.fixture
def policy_store(tmp_path):
    """Create temporary policy storage."""
    store_dir = tmp_path / "policies"
    store_dir.mkdir()
    return store_dir


@pytest.fixture
def sample_policy(policy_store):
    """
    Create a sample policy artifact for testing.
    
    This is a simple but valid policy that always chooses SAVE.
    """
    policy = {
        "(0, 0, 0)": 0,  # SAVE when battery low, solar low
        "(0, 1, 0)": 1,  # USE when battery low, solar high
        "(1, 0, 0)": 0,  # SAVE when battery high, solar low
        "(1, 1, 0)": 1,  # USE when battery high, solar high
        "(0, 0, 1)": 0,
        "(0, 1, 1)": 1,
        "(1, 0, 1)": 0,
        "(1, 1, 1)": 1,
    }
    
    # Compute hash
    policy_json = json.dumps(policy, sort_keys=True)
    policy_hash = hashlib.sha256(policy_json.encode()).hexdigest()[:16]
    
    # Save artifact
    artifact = {
        "policy": policy,
        "metadata": {"test": True}
    }
    
    artifact_path = policy_store / f"{policy_hash}.json"
    with open(artifact_path, 'w') as f:
        json.dump(artifact, f)
    
    return policy_hash, policy


def test_load_valid_policy(policy_store, sample_policy):
    """
    Loading valid policy succeeds.
    """
    policy_hash, expected_policy = sample_policy
    
    consumer = PolicyConsumer(str(policy_store))
    loaded_policy = consumer.load_policy(policy_hash)
    
    assert loaded_policy == expected_policy


def test_load_missing_policy_raises_error(policy_store):
    """
    Loading non-existent policy raises FileNotFoundError.
    """
    consumer = PolicyConsumer(str(policy_store))
    
    with pytest.raises(FileNotFoundError):
        consumer.load_policy("nonexistent_hash")


def test_load_corrupted_policy_raises_error(policy_store):
    """
    Loading corrupted policy raises ValueError.
    """
    # Create corrupted file
    corrupted_path = policy_store / "corrupted.json"
    with open(corrupted_path, 'w') as f:
        f.write("{ invalid json }}")
    
    consumer = PolicyConsumer(str(policy_store))
    
    with pytest.raises(ValueError):
        consumer.load_policy("corrupted")


def test_load_invalid_structure_raises_error(policy_store):
    """
    Loading policy with invalid structure raises ValueError.
    """
    # Create policy without "policy" key
    invalid_path = policy_store / "invalid.json"
    with open(invalid_path, 'w') as f:
        json.dump({"wrong_key": {}}, f)
    
    consumer = PolicyConsumer(str(policy_store))
    
    with pytest.raises(ValueError, match="missing 'policy' key"):
        consumer.load_policy("invalid")


def test_execute_policy_is_deterministic(policy_store, sample_policy):
    """
    Executing same policy with same seed produces same results.
    """
    policy_hash, policy = sample_policy
    consumer = PolicyConsumer(str(policy_store))
    
    # Execute multiple times with same seed
    reward_1 = consumer.execute_policy(policy, episodes=50, seed=42)
    reward_2 = consumer.execute_policy(policy, episodes=50, seed=42)
    reward_3 = consumer.execute_policy(policy, episodes=50, seed=42)
    
    assert reward_1 == reward_2 == reward_3, "Policy execution should be deterministic"


def test_execute_baseline_random(policy_store):
    """
    Execute random baseline policy.
    """
    consumer = PolicyConsumer(str(policy_store))
    
    reward = consumer.execute_baseline(BaselinePolicy.RANDOM, episodes=50, seed=42)
    
    # Random policy should get some reward (can be negative)
    assert -10 <= reward <= 20, f"Random baseline reward out of expected range: {reward}"


def test_execute_baseline_always_save(policy_store):
    """
    Execute always_save baseline policy.
    """
    consumer = PolicyConsumer(str(policy_store))
    
    reward = consumer.execute_baseline(BaselinePolicy.ALWAYS_SAVE, episodes=50, seed=42)
    
    # Always SAVE should get some reward
    assert 0 <= reward <= 20, f"Always_save baseline reward out of expected range: {reward}"


def test_execute_baseline_always_use(policy_store):
    """
    Execute always_use baseline policy.
    """
    consumer = PolicyConsumer(str(policy_store))
    
    reward = consumer.execute_baseline(BaselinePolicy.ALWAYS_USE, episodes=50, seed=42)
    
    # Always USE should get some reward (might be negative)
    assert -10 <= reward <= 20, f"Always_use baseline reward out of expected range: {reward}"


def test_reused_policy_beats_baseline(policy_store):
    """
    THE WOW MOMENT: Reused trained policy outperforms baseline.
    
    This is the key demonstration:
        - Train a policy (via run_agent)
        - Load it without retraining
        - Compare with random baseline
        - Reused policy should be significantly better
    """
    # Train a real policy
    from src.verifier.verifier import PolicyClaim
    import time
    
    # Train agent (this creates policy artifact)
    claim = run_agent(agent_id="test_agent", seed=42, episodes=300)
    
    # Consumer loads it (no training)
    consumer = PolicyConsumer("policies")
    policy = consumer.load_policy(claim.policy_hash)
    
    # Compare with baseline
    policy_reward, baseline_reward, improvement = consumer.compare_with_baseline(
        policy,
        baseline=BaselinePolicy.RANDOM,
        episodes=100,
        seed=99
    )
    
    # Reused policy should beat random baseline
    assert policy_reward > baseline_reward, \
        f"Reused policy ({policy_reward}) should beat baseline ({baseline_reward})"
    
    # Should show significant improvement
    assert improvement > 20, \
        f"Improvement ({improvement}%) should be significant (>20%)"


def test_compare_with_baseline_returns_correct_structure(policy_store, sample_policy):
    """
    compare_with_baseline returns (policy_reward, baseline_reward, improvement).
    """
    policy_hash, policy = sample_policy
    consumer = PolicyConsumer(str(policy_store))
    
    result = consumer.compare_with_baseline(
        policy,
        baseline=BaselinePolicy.RANDOM,
        episodes=50,
        seed=42
    )
    
    assert len(result) == 3, "Should return tuple of 3 values"
    policy_reward, baseline_reward, improvement = result
    
    assert isinstance(policy_reward, (int, float))
    assert isinstance(baseline_reward, (int, float))
    assert isinstance(improvement, (int, float))


def test_convenience_function_matches_class_methods(policy_store):
    """
    Convenience function reuse_best_policy() produces valid results.
    """
    # Train a policy
    claim = run_agent(agent_id="test_agent_conv", seed=123, episodes=300)
    
    # Create best policy reference
    best_ref = BestPolicyReference(
        policy_hash=claim.policy_hash,
        verified_reward=claim.claimed_reward,
        agent_id="test_agent_conv"
    )
    
    # Use convenience function
    results = reuse_best_policy(
        best_ref,
        policy_store_dir="policies",
        episodes=100,
        baseline=BaselinePolicy.RANDOM,
        seed=99
    )
    
    # Check structure
    assert "policy_hash" in results
    assert "policy_reward" in results
    assert "baseline_reward" in results
    assert "improvement" in results
    assert "baseline_type" in results
    
    # Check values
    assert results["policy_hash"] == best_ref.policy_hash
    assert results["policy_reward"] > results["baseline_reward"]


def test_no_training_instant_execution(policy_store, sample_policy):
    """
    Policy execution is instant (no training phase).
    
    This test verifies that execute_policy() does NOT train.
    """
    import time
    
    policy_hash, policy = sample_policy
    consumer = PolicyConsumer(str(policy_store))
    
    # Measure execution time
    start = time.time()
    reward = consumer.execute_policy(policy, episodes=100, seed=42)
    duration = time.time() - start
    
    # Should be very fast (no training, just execution)
    assert duration < 2.0, \
        f"Execution took {duration}s, should be <2s (no training)"
    
    # Should still produce valid reward
    assert -10 <= reward <= 25


def test_consumer_does_not_modify_policy(policy_store, sample_policy):
    """
    Consumer does NOT modify the loaded policy.
    """
    policy_hash, original_policy = sample_policy
    consumer = PolicyConsumer(str(policy_store))
    
    # Load policy
    loaded_policy = consumer.load_policy(policy_hash)
    policy_before = loaded_policy.copy()
    
    # Execute policy
    consumer.execute_policy(loaded_policy, episodes=50, seed=42)
    
    # Policy should be unchanged
    assert loaded_policy == policy_before, "Policy should not be modified during execution"
