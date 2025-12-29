"""
Ledger Tests

Tests for Phase 8: Policy Ledger (Tamper-Evident Memory)

Test coverage:
1. Appending entries creates correct hash chain
2. Reading returns all entries in order
3. Modifying entry detected by chain verification
4. Deleting entry detected by chain verification
5. Ledger persists and reloads correctly
6. Empty ledger is valid
7. Genesis entry has correct previous_hash
8. Duplicate policy hashes allowed
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.ledger.ledger import (
    PolicyLedger,
    LedgerEntry,
    compute_entry_hash,
    verify_chain_integrity
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def temp_ledger():
    """Create a temporary ledger for testing."""
    # Create temp file path (but don't create the file)
    import os
    fd, ledger_path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(ledger_path)  # Delete the empty file
    
    ledger = PolicyLedger(ledger_path)
    yield ledger
    
    # Cleanup
    Path(ledger_path).unlink(missing_ok=True)


# =============================================================================
# TEST 1: APPENDING ENTRIES CREATES HASH CHAIN
# =============================================================================

def test_append_creates_hash_chain(temp_ledger: PolicyLedger):
    """
    Test that appending entries creates correct hash chain.
    
    This is the core functionality:
    - First entry has previous_hash = "genesis"
    - Each subsequent entry chains to previous
    """
    # Append first entry
    entry1 = temp_ledger.append(
        policy_hash="a" * 64,
        verified_reward=15.0,
        agent_id="agent_001"
    )
    
    # Check first entry
    assert entry1.previous_hash == "genesis"
    assert entry1.current_hash != "genesis"
    assert entry1.policy_hash == "a" * 64
    assert entry1.verified_reward == 15.0
    
    # Append second entry
    entry2 = temp_ledger.append(
        policy_hash="b" * 64,
        verified_reward=18.0,
        agent_id="agent_002"
    )
    
    # Check chain
    assert entry2.previous_hash == entry1.current_hash
    assert entry2.current_hash != entry1.current_hash
    
    # Verify integrity
    is_valid, error = temp_ledger.verify_integrity()
    assert is_valid, f"Chain should be valid: {error}"
    
    print("✅ Hash chain created correctly")
    print(f"   Entry 1: previous='genesis', current={entry1.current_hash[:16]}...")
    print(f"   Entry 2: previous={entry2.previous_hash[:16]}..., current={entry2.current_hash[:16]}...")


# =============================================================================
# TEST 2: READING RETURNS ALL ENTRIES IN ORDER
# =============================================================================

def test_read_all_returns_entries_in_order(temp_ledger: PolicyLedger):
    """
    Test that read_all() returns entries in append order.
    """
    # Append multiple entries
    entries = []
    for i in range(5):
        entry = temp_ledger.append(
            policy_hash=f"{i}" * 64,
            verified_reward=float(i * 5),
            agent_id=f"agent_{i:03d}"
        )
        entries.append(entry)
    
    # Read all
    read_entries = temp_ledger.read_all()
    
    # Verify order and content
    assert len(read_entries) == 5
    for i, entry in enumerate(read_entries):
        assert entry.agent_id == f"agent_{i:03d}"
        assert entry.verified_reward == float(i * 5)
        assert entry.policy_hash == f"{i}" * 64
    
    print("✅ Read all entries in correct order")
    print(f"   Total entries: {len(read_entries)}")


# =============================================================================
# TEST 3: MODIFIED ENTRY DETECTED
# =============================================================================

def test_modified_entry_detected(temp_ledger: PolicyLedger):
    """
    Test that modifying an entry breaks the hash chain.
    
    Attack scenario: Someone changes verified_reward
    Defense: Hash chain breaks
    """
    # Append entries
    temp_ledger.append("a" * 64, 15.0, "agent_001")
    temp_ledger.append("b" * 64, 18.0, "agent_002")
    temp_ledger.append("c" * 64, 20.0, "agent_003")
    
    # Verify initial integrity
    is_valid, error = temp_ledger.verify_integrity()
    assert is_valid
    
    # TAMPER: Modify middle entry in storage file
    with open(temp_ledger.storage_path, 'r') as f:
        data = json.load(f)
    
    # Change verified_reward of second entry
    data["entries"][1]["verified_reward"] = 999.0  # Inflated!
    
    with open(temp_ledger.storage_path, 'w') as f:
        json.dump(data, f)
    
    # Reload ledger (should detect tampering)
    with pytest.raises(RuntimeError, match="LEDGER CORRUPTION"):
        PolicyLedger(temp_ledger.storage_path)
    
    print("✅ Modified entry detected (ledger halts)")
    print("   Tamper attempt: changed verified_reward")
    print("   Result: RuntimeError raised, trust preserved")


# =============================================================================
# TEST 4: DELETED ENTRY DETECTED
# =============================================================================

def test_deleted_entry_detected(temp_ledger: PolicyLedger):
    """
    Test that deleting an entry breaks the hash chain.
    
    Attack scenario: Someone removes middle entry
    Defense: previous_hash mismatch detected
    """
    # Append entries
    temp_ledger.append("a" * 64, 15.0, "agent_001")
    temp_ledger.append("b" * 64, 18.0, "agent_002")
    temp_ledger.append("c" * 64, 20.0, "agent_003")
    
    # Verify initial integrity
    is_valid, error = temp_ledger.verify_integrity()
    assert is_valid
    
    # TAMPER: Delete middle entry
    with open(temp_ledger.storage_path, 'r') as f:
        data = json.load(f)
    
    # Remove second entry
    del data["entries"][1]
    data["total_entries"] = 2
    
    with open(temp_ledger.storage_path, 'w') as f:
        json.dump(data, f)
    
    # Reload ledger (should detect tampering)
    with pytest.raises(RuntimeError, match="LEDGER CORRUPTION"):
        PolicyLedger(temp_ledger.storage_path)
    
    print("✅ Deleted entry detected (ledger halts)")
    print("   Tamper attempt: removed middle entry")
    print("   Result: RuntimeError raised, chain break detected")


# =============================================================================
# TEST 5: PERSISTENCE AND RELOAD
# =============================================================================

def test_persistence_and_reload(temp_ledger: PolicyLedger):
    """
    Test that ledger persists to disk and reloads correctly.
    """
    # Append entries
    entries = []
    for i in range(3):
        entry = temp_ledger.append(
            policy_hash=f"{i}" * 64,
            verified_reward=float(i * 10),
            agent_id=f"agent_{i:03d}"
        )
        entries.append(entry)
    
    # Reload ledger from same file
    ledger2 = PolicyLedger(temp_ledger.storage_path)
    
    # Verify same entries
    reloaded = ledger2.read_all()
    assert len(reloaded) == 3
    
    for i, entry in enumerate(reloaded):
        assert entry.agent_id == entries[i].agent_id
        assert entry.policy_hash == entries[i].policy_hash
        assert entry.verified_reward == entries[i].verified_reward
        assert entry.current_hash == entries[i].current_hash
    
    # Verify integrity
    is_valid, error = ledger2.verify_integrity()
    assert is_valid
    
    print("✅ Ledger persists and reloads correctly")
    print(f"   Original entries: {len(entries)}")
    print(f"   Reloaded entries: {len(reloaded)}")
    print(f"   Integrity: ✅ INTACT")


# =============================================================================
# TEST 6: EMPTY LEDGER IS VALID
# =============================================================================

def test_empty_ledger_is_valid(temp_ledger: PolicyLedger):
    """
    Test that empty ledger is considered valid.
    """
    # Check empty ledger
    assert temp_ledger.count() == 0
    
    # Verify integrity
    is_valid, error = temp_ledger.verify_integrity()
    assert is_valid
    assert error is None
    
    # Read all (should be empty list)
    entries = temp_ledger.read_all()
    assert len(entries) == 0
    
    print("✅ Empty ledger is valid")


# =============================================================================
# TEST 7: GENESIS ENTRY HAS CORRECT PREVIOUS_HASH
# =============================================================================

def test_genesis_entry_has_correct_previous_hash(temp_ledger: PolicyLedger):
    """
    Test that first entry has previous_hash = "genesis".
    """
    # Append first entry
    entry = temp_ledger.append(
        policy_hash="first" * 12 + "f" * 4,
        verified_reward=10.0,
        agent_id="first_agent"
    )
    
    # Check genesis
    assert entry.previous_hash == "genesis"
    
    print("✅ Genesis entry correct")
    print(f"   First entry previous_hash: '{entry.previous_hash}'")


# =============================================================================
# TEST 8: DUPLICATE POLICY HASHES ALLOWED
# =============================================================================

def test_duplicate_policy_hashes_allowed(temp_ledger: PolicyLedger):
    """
    Test that same policy_hash can appear multiple times.
    
    This is allowed because:
    - Two agents might submit same policy
    - Same policy verified at different times
    
    Ledger records facts, not uniqueness.
    """
    same_hash = "duplicate" * 5 + "d" * 14
    
    # Append same policy twice
    entry1 = temp_ledger.append(same_hash, 15.0, "agent_001")
    entry2 = temp_ledger.append(same_hash, 15.0, "agent_002")
    
    # Both should be in ledger
    entries = temp_ledger.read_all()
    assert len(entries) == 2
    assert entries[0].policy_hash == same_hash
    assert entries[1].policy_hash == same_hash
    
    # Chain should still be valid
    is_valid, error = temp_ledger.verify_integrity()
    assert is_valid
    
    print("✅ Duplicate policy hashes allowed")
    print(f"   Same policy recorded twice")
    print(f"   Chain integrity: ✅ INTACT")


# =============================================================================
# TEST 9: COMPUTE HASH IS DETERMINISTIC
# =============================================================================

def test_compute_hash_deterministic():
    """
    Test that compute_entry_hash is deterministic.
    
    Same inputs → same hash (always)
    """
    # Compute hash multiple times
    hashes = []
    for _ in range(5):
        h = compute_entry_hash(
            policy_hash="test" * 16,
            verified_reward=15.0,
            agent_id="test_agent",
            timestamp="2025-12-28T12:00:00",
            previous_hash="genesis"
        )
        hashes.append(h)
    
    # All should be identical
    assert len(set(hashes)) == 1
    
    print("✅ Hash computation is deterministic")
    print(f"   Same inputs produced same hash 5 times")


# =============================================================================
# TEST 10: VERIFY CHAIN WITH MANUAL TAMPERING
# =============================================================================

def test_verify_chain_detects_manual_tampering():
    """
    Test verify_chain_integrity function directly.
    """
    # Create valid chain manually
    entry1 = LedgerEntry(
        policy_hash="a" * 64,
        verified_reward=15.0,
        agent_id="agent_001",
        timestamp="2025-12-28T12:00:00",
        previous_hash="genesis",
        current_hash=compute_entry_hash("a" * 64, 15.0, "agent_001", "2025-12-28T12:00:00", "genesis")
    )
    
    entry2 = LedgerEntry(
        policy_hash="b" * 64,
        verified_reward=18.0,
        agent_id="agent_002",
        timestamp="2025-12-28T12:01:00",
        previous_hash=entry1.current_hash,
        current_hash=compute_entry_hash("b" * 64, 18.0, "agent_002", "2025-12-28T12:01:00", entry1.current_hash)
    )
    
    # Valid chain
    is_valid, error = verify_chain_integrity([entry1, entry2])
    assert is_valid
    
    # Tamper with entry1 (change reward but keep hash)
    tampered_entry1 = LedgerEntry(
        policy_hash="a" * 64,
        verified_reward=999.0,  # TAMPERED!
        agent_id="agent_001",
        timestamp="2025-12-28T12:00:00",
        previous_hash="genesis",
        current_hash=entry1.current_hash  # Old hash (incorrect now)
    )
    
    # Should detect tampering
    is_valid, error = verify_chain_integrity([tampered_entry1, entry2])
    assert not is_valid
    assert "hash mismatch" in error.lower()
    
    print("✅ Chain verification detects tampering")
    print(f"   Tampered entry: verified_reward changed")
    print(f"   Detection: hash mismatch")


# =============================================================================
# MAIN (for manual testing)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 8 — POLICY LEDGER TESTS")
    print("=" * 70)
    print()
    
    import tempfile
    
    # Create temp ledger
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        ledger_path = f.name
    ledger = PolicyLedger(ledger_path)
    
    print("Test 1: Append creates hash chain")
    print("-" * 70)
    test_append_creates_hash_chain(ledger)
    print()
    
    # Create new ledger for each test
    Path(ledger_path).unlink()
    ledger = PolicyLedger(ledger_path)
    
    print("Test 2: Read all returns entries in order")
    print("-" * 70)
    test_read_all_returns_entries_in_order(ledger)
    print()
    
    # New ledger
    Path(ledger_path).unlink()
    ledger = PolicyLedger(ledger_path)
    
    print("Test 5: Persistence and reload")
    print("-" * 70)
    test_persistence_and_reload(ledger)
    print()
    
    # New ledger
    Path(ledger_path).unlink()
    ledger = PolicyLedger(ledger_path)
    
    print("Test 6: Empty ledger is valid")
    print("-" * 70)
    test_empty_ledger_is_valid(ledger)
    print()
    
    # New ledger
    Path(ledger_path).unlink()
    ledger = PolicyLedger(ledger_path)
    
    print("Test 7: Genesis entry correct")
    print("-" * 70)
    test_genesis_entry_has_correct_previous_hash(ledger)
    print()
    
    # New ledger
    Path(ledger_path).unlink()
    ledger = PolicyLedger(ledger_path)
    
    print("Test 8: Duplicate hashes allowed")
    print("-" * 70)
    test_duplicate_policy_hashes_allowed(ledger)
    print()
    
    print("Test 9: Hash computation deterministic")
    print("-" * 70)
    test_compute_hash_deterministic()
    print()
    
    print("Test 10: Chain verification detects tampering")
    print("-" * 70)
    test_verify_chain_detects_manual_tampering()
    print()
    
    # Cleanup
    Path(ledger_path).unlink(missing_ok=True)
    
    print("=" * 70)
    print("ALL TESTS PASSED ✅")
    print("=" * 70)
