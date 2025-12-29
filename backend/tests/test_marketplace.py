"""
Tests for Phase 9 — Marketplace (Policy Selection)

Test Coverage:
    1. Empty ledger → None
    2. Single entry → That policy
    3. Multiple entries → Highest reward wins
    4. Tie-breaking → Earlier timestamp wins
    5. Ranked list → Correct order
    6. Determinism → Same result every time
    7. No side effects → Ledger unchanged
    8. Convenience function → Same as class method
"""

import pytest
import time
from src.marketplace.ranking import PolicyMarketplace, BestPolicyReference, select_best_policy
from src.ledger.ledger import PolicyLedger


@pytest.fixture
def temp_ledger(tmp_path):
    """Create temporary ledger for testing."""
    ledger_path = tmp_path / "test_marketplace.json"
    return PolicyLedger(str(ledger_path))


def test_empty_ledger_returns_none(temp_ledger):
    """
    Edge Case: Empty ledger
    Expected: Returns None (no crash, no defaults)
    """
    marketplace = PolicyMarketplace(temp_ledger)
    best = marketplace.get_best_policy()
    
    assert best is None, "Empty ledger should return None"


def test_single_entry_is_best_by_definition(temp_ledger):
    """
    Edge Case: Single entry
    Expected: That policy is best (by definition)
    """
    # Append single entry
    temp_ledger.append(
        policy_hash="hash_single",
        verified_reward=10.5,
        agent_id="agent_001"
    )
    
    marketplace = PolicyMarketplace(temp_ledger)
    best = marketplace.get_best_policy()
    
    assert best is not None
    assert best.policy_hash == "hash_single"
    assert best.verified_reward == 10.5
    assert best.agent_id == "agent_001"


def test_highest_reward_wins(temp_ledger):
    """
    Ranking Rule: Highest verified_reward wins
    """
    # Append entries with different rewards
    temp_ledger.append("hash_low", 5.0, "agent_001")
    time.sleep(0.01)  # Ensure different timestamps
    temp_ledger.append("hash_high", 15.0, "agent_002")
    time.sleep(0.01)
    temp_ledger.append("hash_medium", 10.0, "agent_003")
    
    marketplace = PolicyMarketplace(temp_ledger)
    best = marketplace.get_best_policy()
    
    assert best is not None
    assert best.policy_hash == "hash_high"
    assert best.verified_reward == 15.0
    assert best.agent_id == "agent_002"


def test_tie_breaker_earlier_timestamp_wins(temp_ledger):
    """
    Tie-Breaking Rule: Earlier timestamp wins
    """
    # Append entries with same reward but different timestamps
    temp_ledger.append("hash_first", 10.0, "agent_001")
    time.sleep(0.01)  # Ensure timestamp difference
    temp_ledger.append("hash_second", 10.0, "agent_002")
    time.sleep(0.01)
    temp_ledger.append("hash_third", 10.0, "agent_003")
    
    marketplace = PolicyMarketplace(temp_ledger)
    best = marketplace.get_best_policy()
    
    # Earlier timestamp should win
    assert best is not None
    assert best.policy_hash == "hash_first"
    assert best.agent_id == "agent_001"


def test_ranked_list_correct_order(temp_ledger):
    """
    get_ranked_policies returns all policies in correct order.
    """
    # Append entries with known ranking
    temp_ledger.append("hash_3rd", 5.0, "agent_003")
    time.sleep(0.01)
    temp_ledger.append("hash_1st", 15.0, "agent_001")
    time.sleep(0.01)
    temp_ledger.append("hash_2nd", 10.0, "agent_002")
    
    marketplace = PolicyMarketplace(temp_ledger)
    ranked = marketplace.get_ranked_policies()
    
    assert len(ranked) == 3
    assert ranked[0].policy_hash == "hash_1st"  # 15.0
    assert ranked[1].policy_hash == "hash_2nd"  # 10.0
    assert ranked[2].policy_hash == "hash_3rd"  # 5.0


def test_ranked_list_empty_ledger(temp_ledger):
    """
    get_ranked_policies on empty ledger returns empty list.
    """
    marketplace = PolicyMarketplace(temp_ledger)
    ranked = marketplace.get_ranked_policies()
    
    assert ranked == []


def test_selection_is_deterministic(temp_ledger):
    """
    Determinism: Same ledger → Same result every time
    """
    # Append multiple entries
    temp_ledger.append("hash_A", 12.0, "agent_A")
    time.sleep(0.01)
    temp_ledger.append("hash_B", 15.0, "agent_B")
    time.sleep(0.01)
    temp_ledger.append("hash_C", 10.0, "agent_C")
    
    marketplace = PolicyMarketplace(temp_ledger)
    
    # Call multiple times
    best_1 = marketplace.get_best_policy()
    best_2 = marketplace.get_best_policy()
    best_3 = marketplace.get_best_policy()
    
    assert best_1 == best_2 == best_3
    assert best_1.policy_hash == "hash_B"


def test_no_side_effects_on_ledger(temp_ledger):
    """
    Marketplace does NOT modify ledger.
    """
    # Append entries
    temp_ledger.append("hash_1", 10.0, "agent_1")
    temp_ledger.append("hash_2", 20.0, "agent_2")
    
    entries_before = temp_ledger.read_all()
    
    marketplace = PolicyMarketplace(temp_ledger)
    marketplace.get_best_policy()
    marketplace.get_ranked_policies()
    
    entries_after = temp_ledger.read_all()
    
    # Ledger should be unchanged
    assert entries_before == entries_after


def test_convenience_function_matches_class_method(temp_ledger):
    """
    Convenience function select_best_policy() returns same result as class method.
    """
    temp_ledger.append("hash_best", 25.0, "agent_best")
    temp_ledger.append("hash_other", 10.0, "agent_other")
    
    marketplace = PolicyMarketplace(temp_ledger)
    best_via_class = marketplace.get_best_policy()
    best_via_function = select_best_policy(temp_ledger)
    
    assert best_via_class == best_via_function


def test_multiple_ties_all_resolved_deterministically(temp_ledger):
    """
    Multiple policies with same reward → All ties resolved by timestamp.
    """
    # Append 5 entries with same reward
    temp_ledger.append("hash_t1", 10.0, "agent_1")
    time.sleep(0.01)
    temp_ledger.append("hash_t2", 10.0, "agent_2")
    time.sleep(0.01)
    temp_ledger.append("hash_t3", 10.0, "agent_3")
    time.sleep(0.01)
    temp_ledger.append("hash_t4", 10.0, "agent_4")
    time.sleep(0.01)
    temp_ledger.append("hash_t5", 10.0, "agent_5")
    
    marketplace = PolicyMarketplace(temp_ledger)
    best = marketplace.get_best_policy()
    
    # First entry should win (earliest timestamp)
    assert best.policy_hash == "hash_t1"
    assert best.agent_id == "agent_1"
