"""
🚀 SIMPLE PARALLEL DEMO — 6 Agents in Sequence (Fast) 🎯

Simplified version that trains agents sequentially but quickly.
Perfect for demonstration without multiprocessing complexity.
"""

import time
from datetime import datetime

print("=" * 80)
print("🚀 FAST SEQUENTIAL DEMO — 6 AGENTS TRAINING 🎯")
print("=" * 80)
print()
print("⚡ FAST MODE: 150 episodes per agent")
print()
print("This demonstrates decentralized learning:")
print("  • 6 independent agents train with different seeds")
print("  • Each agent has its own environment instance")
print("  • No coordination between agents")
print()
print("=" * 80)
print()

overall_start = time.time()

# -----------------------------------------------------------------------------
# STEP 1: Train All Agents Sequentially
# -----------------------------------------------------------------------------
print("📚 STEP 1: Train 6 Independent Agents")
print("-" * 80)

from src.agent.runner import run_agent

AGENT_CONFIGS = [
    ("agent_alpha", 42, 150),
    ("agent_beta", 99, 150),
    ("agent_gamma", 123, 150),
    ("agent_delta", 256, 150),
    ("agent_epsilon", 777, 150),
    ("agent_zeta", 1024, 150),
]

claims = []
total_training_time = 0

for agent_id, seed, episodes in AGENT_CONFIGS:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🤖 {agent_id} → Starting (seed={seed}, episodes={episodes})")
    
    start_time = time.time()
    claim = run_agent(agent_id, seed, episodes)
    elapsed = time.time() - start_time
    total_training_time += elapsed
    
    claims.append(claim)
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] ✅ {agent_id} → Done in {elapsed:.1f}s | Reward: {claim.claimed_reward:.3f}")

training_time = time.time() - overall_start

print(f"\n{'=' * 80}")
print(f"✅ All {len(claims)} agents trained in {training_time:.1f}s")
print("=" * 80)
print()

# -----------------------------------------------------------------------------
# STEP 2: Display Results
# -----------------------------------------------------------------------------
print("📊 STEP 2: Training Results")
print("-" * 80)

claims_sorted = sorted(claims, key=lambda c: c.claimed_reward, reverse=True)
for i, claim in enumerate(claims_sorted, 1):
    bar = "█" * int(claim.claimed_reward * 2)
    print(f"  {i}. {claim.agent_id:15s} → {claim.claimed_reward:7.3f} {bar}")
print()

# -----------------------------------------------------------------------------
# STEP 3: Verify All Claims
# -----------------------------------------------------------------------------
print("=" * 80)
print("🔍 STEP 3: Verify All Claims")
print("-" * 80)

from src.verifier.verifier import PolicyVerifier

verifier = PolicyVerifier()
verified_results = []

verify_start = time.time()
for claim in claims:
    result = verifier.verify(claim)
    verified_results.append(result)
    
    status_icon = "✅" if result.status.value == "VALID" else "❌"
    print(f"{status_icon} {claim.agent_id:15s} → Verified: {result.verified_reward:.3f}")

verify_time = time.time() - verify_start
valid_count = sum(1 for r in verified_results if r.status.value == "VALID")
print(f"\n✅ Verified {valid_count}/{len(claims)} policies in {verify_time:.1f}s")
print()

# -----------------------------------------------------------------------------
# STEP 4: Record in Ledger
# -----------------------------------------------------------------------------
print("=" * 80)
print("📝 STEP 4: Record in Tamper-Evident Ledger")
print("-" * 80)

from src.ledger.ledger import PolicyLedger, verify_chain_integrity

ledger_file = "demo_parallel_ledger.json"
ledger = PolicyLedger(ledger_file)

recorded_count = 0
for claim, result in zip(claims, verified_results):
    if result.status.value == "VALID":
        entry = ledger.append(
            policy_hash=claim.policy_hash,
            verified_reward=result.verified_reward,
            agent_id=claim.agent_id
        )
        recorded_count += 1
        print(f"✅ {claim.agent_id:15s} → Recorded (block #{entry.index})")

print(f"\n✅ Ledger contains {len(ledger.read_all())} entries")

# Verify chain integrity
entries = ledger.read_all()
is_intact = verify_chain_integrity(entries)
print(f"🔗 Hash chain: {'✅ INTACT' if is_intact else '❌ BROKEN'}")
print()

# -----------------------------------------------------------------------------
# STEP 5: Marketplace Selection
# -----------------------------------------------------------------------------
print("=" * 80)
print("🏆 STEP 5: Marketplace Selects Best Policy")
print("-" * 80)

from src.marketplace.ranking import select_best_policy, PolicyMarketplace

best = select_best_policy(ledger)

if best:
    print(f"🏆 WINNER: {best.agent_id}")
    print(f"   Reward: {best.verified_reward:.3f}")
    print(f"   Hash: {best.policy_hash[:16]}...")
    print()
    
    # Show full rankings
    marketplace = PolicyMarketplace(ledger)
    rankings = marketplace.get_ranked_policies()
    print("Full Rankings:")
    for i, policy in enumerate(rankings, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"  {medal} {i}. {policy.agent_id:15s} → {policy.verified_reward:.3f}")
else:
    print("❌ No valid policies found")
    exit(1)
print()

# -----------------------------------------------------------------------------
# STEP 6: Policy Reuse - THE WOW MOMENT
# -----------------------------------------------------------------------------
print("=" * 80)
print("🎯 STEP 6: Policy Reuse — THE WOW MOMENT")
print("-" * 80)

from src.consumer.reuse import reuse_best_policy

print("🔄 Consumer reusing best policy (NO TRAINING)...")
reuse_start = time.time()
result = reuse_best_policy(best, seed=9999)
reuse_time = time.time() - reuse_start

print(f"\n✅ Policy Reuse Complete in {reuse_time:.2f}s!")
print(f"   Best Policy: {result['agent_id']}")
print(f"   Verified: {result['verified_reward']:.3f}")
print(f"   Reused: {result['policy_reward']:.3f}")
print(f"   Baseline: {result['baseline_reward']:.3f}")
print(f"   Improvement: {result['improvement']:+.1f}%")
print()

# -----------------------------------------------------------------------------
# FINAL SUMMARY
# -----------------------------------------------------------------------------
total_time = time.time() - overall_start

print("=" * 80)
print("🎉 DEMO COMPLETE!")
print("=" * 80)
print()
print(f"⏱️  Total Demo Time: {total_time:.1f}s")
print()
print("✅ Complete Workflow:")
print(f"   • Training: {training_time:.1f}s ({len(claims)} agents)")
print(f"   • Verification: {verify_time:.1f}s ({valid_count} policies)")
print(f"   • Ledger: {recorded_count} entries recorded")
print(f"   • Marketplace: Best policy selected")
print(f"   • Reuse: {reuse_time:.2f}s (instant!)")
print()
print("💡 This demonstrates:")
print("   • Decentralized learning (independent agents)")
print("   • Deterministic verification")
print("   • Tamper-evident ledger (hash-chained)")
print("   • Intelligent policy marketplace")
print("   • Zero-training policy reuse")
print(f"   • {result['improvement']:+.1f}% improvement over random baseline")
print()
print(f"📁 Ledger: {ledger_file}")
print(f"📁 Policies: policies/ directory")
print()
