"""
Verification Layer Demo

Demonstrates the core novelty of PolicyLedger:
"Trust is derived from replayability, not reputation."

This script:
1. Creates legitimate agent claims
2. Verifies them through deterministic replay
3. Tests adversarial scenarios (inflated rewards, tampered policies)
4. Shows binary verification decisions
"""

from src.agent.runner import run_agent, PolicyClaim
from src.verifier.verifier import PolicyVerifier, VerificationStatus, verify_claim
from src.agent.policy import serialize_policy, hash_policy


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_claim(claim: PolicyClaim):
    """Print policy claim details."""
    print(f"Agent ID: {claim.agent_id}")
    print(f"Environment: {claim.env_id}")
    print(f"Policy Hash: {claim.policy_hash[:16]}...")
    print(f"Claimed Reward: {claim.claimed_reward:.3f}")


def print_result(result):
    """Print verification result."""
    print(f"\nVerification Result:")
    print(f"  Status: {result.status.value}")
    print(f"  Verified Reward: {result.verified_reward}")
    print(f"  Reason: {result.reason}")


def demo_valid_claim():
    """Demo 1: Valid claim passes verification."""
    print_section("DEMO 1: Valid Claim Passes Verification")
    
    print("Training agent...")
    claim = run_agent(agent_id="honest_agent_001", seed=42, episodes=500)
    
    print("\nAgent trained successfully!")
    print_claim(claim)
    
    print("\n" + "-" * 70)
    print("Verifying claim through deterministic replay...")
    print("-" * 70)
    
    verifier = PolicyVerifier(reward_threshold=1e-6)
    result = verifier.verify(claim)
    
    print_result(result)
    
    if result.status == VerificationStatus.VALID:
        print("\n✅ VERIFICATION PASSED")
        print("   Agent's claim is reproducible and trustworthy.")
    
    return claim


def demo_inflated_reward(valid_claim: PolicyClaim):
    """Demo 2: Inflated reward claim fails verification."""
    print_section("DEMO 2: Inflated Reward Claim Fails Verification")
    
    print("Scenario: Malicious agent inflates claimed reward")
    print("Original claimed reward:", valid_claim.claimed_reward)
    
    # Create inflated claim
    inflated_claim = PolicyClaim(
        agent_id="malicious_agent_001",
        env_id=valid_claim.env_id,
        policy_hash=valid_claim.policy_hash,
        policy_artifact=valid_claim.policy_artifact,
        claimed_reward=valid_claim.claimed_reward + 15.0  # Inflate by 15
    )
    
    print("Inflated claimed reward:", inflated_claim.claimed_reward)
    print("\n" + "-" * 70)
    print("Verifying inflated claim...")
    print("-" * 70)
    
    verifier = PolicyVerifier(reward_threshold=1e-6)
    result = verifier.verify(inflated_claim)
    
    print_result(result)
    
    if result.status == VerificationStatus.INVALID:
        print("\n❌ VERIFICATION FAILED (AS EXPECTED)")
        print("   Inflated reward detected and rejected.")
        print(f"   Actual reward: {result.verified_reward:.3f}")
        print(f"   Claimed reward: {inflated_claim.claimed_reward:.3f}")
        print(f"   Difference: {inflated_claim.claimed_reward - result.verified_reward:.3f}")


def demo_hash_mismatch(valid_claim: PolicyClaim):
    """Demo 3: Policy hash mismatch fails verification."""
    print_section("DEMO 3: Policy Hash Mismatch Fails Verification")
    
    print("Scenario: Policy artifact tampered after submission")
    print("Original hash:", valid_claim.policy_hash[:16] + "...")
    
    # Create tampered claim (wrong hash)
    tampered_claim = PolicyClaim(
        agent_id="tampered_agent_001",
        env_id=valid_claim.env_id,
        policy_hash="a" * 64,  # Wrong hash
        policy_artifact=valid_claim.policy_artifact,
        claimed_reward=valid_claim.claimed_reward
    )
    
    print("Submitted hash:", tampered_claim.policy_hash[:16] + "...")
    print("\n" + "-" * 70)
    print("Verifying tampered claim...")
    print("-" * 70)
    
    verifier = PolicyVerifier(reward_threshold=1e-6)
    result = verifier.verify(tampered_claim)
    
    print_result(result)
    
    if result.status == VerificationStatus.INVALID:
        print("\n❌ VERIFICATION FAILED (AS EXPECTED)")
        print("   Hash mismatch detected - prevents post-submission tampering.")


def demo_incomplete_policy():
    """Demo 4: Incomplete policy fails verification."""
    print_section("DEMO 4: Incomplete Policy Fails Verification")
    
    print("Scenario: Agent submits incomplete policy")
    
    # Create incomplete policy (only 2 state-action pairs)
    incomplete_policy = {
        (0, 4, 0): 0,
        (0, 4, 1): 1
    }
    
    incomplete_artifact = serialize_policy(incomplete_policy)
    incomplete_hash = hash_policy(incomplete_artifact)
    
    incomplete_claim = PolicyClaim(
        agent_id="incomplete_agent_001",
        env_id="energy_slot_env_seed_42_slots_24",
        policy_hash=incomplete_hash,
        policy_artifact=incomplete_artifact,
        claimed_reward=10.0
    )
    
    print(f"Policy has only {len(incomplete_policy)} state-action pairs")
    print("(Full policy needs ~100+ pairs for 24-step environment)")
    
    print("\n" + "-" * 70)
    print("Verifying incomplete claim...")
    print("-" * 70)
    
    verifier = PolicyVerifier(reward_threshold=1e-6)
    result = verifier.verify(incomplete_claim)
    
    print_result(result)
    
    if result.status == VerificationStatus.INVALID:
        print("\n❌ VERIFICATION FAILED (AS EXPECTED)")
        print("   Incomplete policy cannot be deterministically replayed.")


def demo_multiple_agents():
    """Demo 5: Multiple independent agents with different rewards."""
    print_section("DEMO 5: Multiple Independent Agents")
    
    print("Training multiple agents with different configurations...\n")
    
    # Train 3 agents with different parameters
    agents = [
        ("Agent A (500 episodes)", 42, 500),
        ("Agent B (100 episodes)", 42, 100),
        ("Agent C (different seed)", 99, 500),
    ]
    
    verifier = PolicyVerifier(reward_threshold=1e-6)
    results = []
    
    for name, seed, episodes in agents:
        print(f"Training {name}...")
        claim = run_agent(agent_id=name, seed=seed, episodes=episodes)
        result = verifier.verify(claim)
        results.append((name, result))
        
        print(f"  Claimed: {claim.claimed_reward:.3f}")
        print(f"  Verified: {result.verified_reward:.3f}")
        print(f"  Status: {result.status.value}")
        print()
    
    print("-" * 70)
    print("Summary:")
    print("-" * 70)
    
    for name, result in results:
        status_symbol = "✅" if result.status == VerificationStatus.VALID else "❌"
        print(f"{status_symbol} {name:30s} Reward: {result.verified_reward:.3f}")
    
    print("\nAll agents verified independently through deterministic replay.")
    print("Different training configurations → different verified rewards.")


def demo_determinism_check(valid_claim: PolicyClaim):
    """Demo 6: Verify replay determinism."""
    print_section("DEMO 6: Replay Determinism Verification")
    
    print("Running same policy multiple times to verify determinism...\n")
    
    verifier = PolicyVerifier(reward_threshold=1e-6)
    
    # Run verification 5 times
    rewards = []
    for i in range(5):
        result = verifier.verify(valid_claim)
        rewards.append(result.verified_reward)
        print(f"Run {i+1}: {result.verified_reward:.6f}")
    
    # Check if all identical
    is_deterministic = len(set(rewards)) == 1
    
    print("\n" + "-" * 70)
    if is_deterministic:
        print("✅ DETERMINISM CONFIRMED")
        print("   All 5 replays produced identical reward.")
        print("   Verification is reproducible and trustworthy.")
    else:
        print("❌ NON-DETERMINISM DETECTED (SYSTEM ERROR)")
        print("   Different replays produced different rewards.")
        print("   This should never happen!")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  PHASE 7 — VERIFICATION LAYER DEMONSTRATION")
    print("  PolicyLedger: Trust through Replayability")
    print("=" * 70)
    
    # Demo 1: Valid claim
    valid_claim = demo_valid_claim()
    
    # Demo 2: Inflated reward
    demo_inflated_reward(valid_claim)
    
    # Demo 3: Hash mismatch
    demo_hash_mismatch(valid_claim)
    
    # Demo 4: Incomplete policy
    demo_incomplete_policy()
    
    # Demo 5: Multiple agents
    demo_multiple_agents()
    
    # Demo 6: Determinism check
    demo_determinism_check(valid_claim)
    
    # Final summary
    print_section("SUMMARY")
    print("Phase 7 Implementation Complete ✅\n")
    print("Core Novelty Demonstrated:")
    print("  • Valid claims pass verification")
    print("  • Inflated rewards detected and rejected")
    print("  • Hash mismatches detected and rejected")
    print("  • Incomplete policies rejected")
    print("  • Replay is deterministic and reproducible")
    print("  • Multiple independent agents verified correctly")
    print()
    print("Key Principle:")
    print('  "Trust is derived from replayability, not reputation."')
    print()
    print("Next Steps:")
    print("  → Phase 8: Policy Ledger (immutable storage)")
    print("  → Phase 9: Marketplace (ranking verified policies)")
    print("  → Phase 10: Policy Reuse (the wow moment)")
    print()


if __name__ == "__main__":
    main()
