"""
End-to-End Demo: Training → Verification → Ledger

This demonstrates the complete PolicyLedger workflow:
1. Agents train policies
2. Verifier verifies claims
3. Ledger records verified policies
4. Chain integrity is maintained
5. Tampering detection works
"""

from pathlib import Path
from src.agent.runner import run_agent
from src.verifier import PolicyVerifier
from src.ledger import PolicyLedger


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def main():
    """Run end-to-end demo."""
    print("\n" + "=" * 70)
    print("  PHASE 7 + 8 — VERIFICATION & LEDGER INTEGRATION")
    print("  PolicyLedger: Trust through Replayability + Immutable Memory")
    print("=" * 70)
    
    # Setup
    ledger_path = "demo_ledger.json"
    Path(ledger_path).unlink(missing_ok=True)  # Clean start
    
    ledger = PolicyLedger(ledger_path)
    verifier = PolicyVerifier(reward_threshold=1e-6)
    
    # =========================================================================
    # DEMO 1: Multiple Agents → Verification → Ledger
    # =========================================================================
    
    print_section("DEMO 1: Complete Workflow")
    
    print("Training 3 agents with different configurations...\n")
    
    agents = [
        ("agent_001", 42, 500),
        ("agent_002", 99, 300),
        ("agent_003", 42, 400),
    ]
    
    for agent_id, seed, episodes in agents:
        print(f"Agent: {agent_id}")
        print("-" * 70)
        
        # Step 1: Train
        print(f"  [1] Training ({episodes} episodes, seed {seed})...")
        claim = run_agent(agent_id=agent_id, seed=seed, episodes=episodes)
        print(f"      Claimed reward: {claim.claimed_reward:.3f}")
        
        # Step 2: Verify
        print(f"  [2] Verifying through deterministic replay...")
        result = verifier.verify(claim)
        print(f"      Status: {result.status.value}")
        print(f"      Verified reward: {result.verified_reward:.3f}")
        
        # Step 3: Append to ledger (only if valid)
        if result.status.value == "VALID":
            print(f"  [3] Recording to ledger...")
            entry = ledger.append(
                policy_hash=claim.policy_hash,
                verified_reward=result.verified_reward,
                agent_id=agent_id
            )
            print(f"      Ledger entry: {entry.current_hash[:16]}...")
            print(f"      ✅ Policy recorded immutably")
        else:
            print(f"      ❌ REJECTED - not recorded to ledger")
        
        print()
    
    # =========================================================================
    # DEMO 2: Ledger State
    # =========================================================================
    
    print_section("DEMO 2: Ledger State")
    
    entries = ledger.read_all()
    print(f"Total entries in ledger: {len(entries)}")
    print()
    
    for i, entry in enumerate(entries):
        print(f"Entry {i}:")
        print(f"  Agent: {entry.agent_id}")
        print(f"  Verified Reward: {entry.verified_reward:.3f}")
        print(f"  Policy Hash: {entry.policy_hash[:16]}...")
        print(f"  Previous Hash: {entry.previous_hash[:16] if entry.previous_hash != 'genesis' else 'genesis'}...")
        print(f"  Current Hash: {entry.current_hash[:16]}...")
        print()
    
    # =========================================================================
    # DEMO 3: Chain Integrity Verification
    # =========================================================================
    
    print_section("DEMO 3: Chain Integrity Verification")
    
    is_valid, error = ledger.verify_integrity()
    
    if is_valid:
        print("✅ CHAIN INTACT")
        print("   All entries properly hash-chained")
        print("   No tampering detected")
    else:
        print(f"❌ CHAIN COMPROMISED: {error}")
    
    print()
    print("Chain structure:")
    print("  Entry 0: genesis → [hash0]")
    for i in range(1, len(entries)):
        print(f"  Entry {i}: [hash{i-1}] → [hash{i}]")
    
    # =========================================================================
    # DEMO 4: Persistence
    # =========================================================================
    
    print_section("DEMO 4: Persistence & Reload")
    
    print(f"Ledger persisted to: {ledger_path}")
    print()
    
    # Reload ledger
    print("Reloading ledger from disk...")
    ledger2 = PolicyLedger(ledger_path)
    
    reloaded_entries = ledger2.read_all()
    print(f"✅ Loaded {len(reloaded_entries)} entries")
    
    # Verify integrity after reload
    is_valid2, error2 = ledger2.verify_integrity()
    print(f"   Integrity after reload: {'✅ INTACT' if is_valid2 else '❌ COMPROMISED'}")
    
    # =========================================================================
    # DEMO 5: Tamper Detection (Simulation)
    # =========================================================================
    
    print_section("DEMO 5: Tamper Detection")
    
    print("Simulating tampering scenario...")
    print("(In real attack, someone would edit the JSON file)")
    print()
    
    # Create a tampered entry manually
    from src.ledger.ledger import LedgerEntry, verify_chain_integrity
    
    # Get original entries
    original_entries = ledger.read_all()
    
    # Tamper with middle entry (change reward)
    if len(original_entries) >= 2:
        tampered_entries = original_entries.copy()
        middle_idx = 1
        
        print(f"Original Entry {middle_idx}:")
        print(f"  Verified Reward: {original_entries[middle_idx].verified_reward:.3f}")
        print()
        
        # Create tampered version (change reward but keep hash - this breaks chain)
        tampered_entry = LedgerEntry(
            policy_hash=original_entries[middle_idx].policy_hash,
            verified_reward=999.0,  # TAMPERED!
            agent_id=original_entries[middle_idx].agent_id,
            timestamp=original_entries[middle_idx].timestamp,
            previous_hash=original_entries[middle_idx].previous_hash,
            current_hash=original_entries[middle_idx].current_hash  # Old hash (now invalid)
        )
        
        tampered_entries[middle_idx] = tampered_entry
        
        print(f"Tampered Entry {middle_idx}:")
        print(f"  Verified Reward: {tampered_entry.verified_reward:.3f} (INFLATED!)")
        print()
        
        # Verify chain detects tampering
        is_valid_tampered, error_tampered = verify_chain_integrity(tampered_entries)
        
        if not is_valid_tampered:
            print("❌ TAMPERING DETECTED")
            print(f"   Reason: {error_tampered}")
            print("   Trust preserved by halting!")
        else:
            print("⚠️  WARNING: Tampering not detected (should not happen)")
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    
    print_section("SUMMARY")
    
    print("Phase 7 + 8 Integration Complete ✅\n")
    print("Demonstrated:")
    print("  • Training → Verification → Ledger pipeline")
    print("  • Multiple agents recorded independently")
    print("  • Hash chain integrity maintained")
    print("  • Persistence and reload working")
    print("  • Tampering detection functional")
    print()
    print("Key Properties:")
    print(f"  • Ledger entries: {ledger.count()}")
    print(f"  • Chain integrity: {'✅ INTACT' if is_valid else '❌ COMPROMISED'}")
    print(f"  • Storage: {ledger_path}")
    print()
    print("Core Principles Validated:")
    print('  • Phase 7: "Trust derived from replayability"')
    print('  • Phase 8: "Immutable record through hash chaining"')
    print()
    print("Next Steps:")
    print("  → Phase 9: Marketplace (rank verified policies)")
    print("  → Phase 10: Policy Reuse (the wow moment)")
    print()
    
    # Cleanup prompt
    print(f"Demo ledger saved to: {ledger_path}")
    print("(You can inspect the JSON file or delete it)")
    print()


if __name__ == "__main__":
    main()
