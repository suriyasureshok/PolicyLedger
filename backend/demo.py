"""
🚀 CYBER DEFENSE DEMO — 6 Agents Training Decision Policies 🎯

Demonstrates PolicyLedger with simulated cyber defense environment.
This is a DECISION-LEVEL simulation, not a real cybersecurity system.

Shows complete workflow:
- Decentralized agent training (cyber defense policies)
- Deterministic verification replay
- Tamper-evident ledger storage
- Policy marketplace ranking
- Zero-training policy reuse
"""

import time
from datetime import datetime

print("=" * 80)
print("🚀 CYBER DEFENSE POLICY MARKETPLACE DEMO 🎯")
print("=" * 80)
print()
print("⚡ Training: 500 episodes per agent for robust policy learning")
print()
print("This demonstrates decentralized learning for simulated cyber defense:")
print("  • 6 independent agents train defense policies with different seeds")
print("  • Each agent learns decision-level cyber defense strategies")
print("  • No coordination between agents (decentralized)")
print("  • Policies are verified through deterministic replay")
print()
print("=" * 80)
print()

overall_start = time.time()

# -----------------------------------------------------------------------------
# STEP 1: Train All Agents Sequentially
# -----------------------------------------------------------------------------
print("📚 STEP 1: Train 6 Independent Cyber Defense Agents")
print("-" * 80)

from src.agent.runner import run_agent

AGENT_CONFIGS = [
    ("agent_alpha", 42, 500),
    ("agent_beta", 99, 500),
    ("agent_gamma", 123, 500),
    ("agent_delta", 256, 500),
    ("agent_epsilon", 777, 500),
    ("agent_zeta", 1024, 500),
]

claims = []
total_training_time = 0

for agent_id, seed, episodes in AGENT_CONFIGS:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🤖 {agent_id} → Training defense policy (seed={seed}, episodes={episodes})")
    
    start_time = time.time()
    claim = run_agent(agent_id, seed, episodes)
    elapsed = time.time() - start_time
    total_training_time += elapsed
    
    claims.append(claim)
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] ✅ {agent_id} → Done in {elapsed:.1f}s | Defense Score: {claim.claimed_reward:.3f}")

training_time = time.time() - overall_start

print(f"\n{'=' * 80}")
print(f"✅ All {len(claims)} agents trained in {training_time:.1f}s")
print("=" * 80)
print()

# -----------------------------------------------------------------------------
# STEP 2: Display Results
# -----------------------------------------------------------------------------
print("📊 STEP 2: Defense Policy Training Results")
print("-" * 80)

claims_sorted = sorted(claims, key=lambda c: c.claimed_reward, reverse=True)
for i, claim in enumerate(claims_sorted, 1):
    bar = "█" * max(0, int(claim.claimed_reward * 2))
    print(f"  {i}. {claim.agent_id:15s} → {claim.claimed_reward:7.3f} {bar}")
print()

# -----------------------------------------------------------------------------
# STEP 3: Verify All Claims
# -----------------------------------------------------------------------------
print("=" * 80)
print("🔍 STEP 3: Verify Defense Policies via Deterministic Replay")
print("-" * 80)
print("Verifier replays each policy in simulation to confirm claimed scores...")
print()

from src.verifier.verifier import PolicyVerifier

verifier = PolicyVerifier()
verified_results = []

verify_start = time.time()
for claim in claims:
    result = verifier.verify(claim)
    verified_results.append(result)
    
    status_icon = "✅" if result.status.value == "VALID" else "❌"
    print(f"{status_icon} {claim.agent_id:15s} → Verified Defense Score: {result.verified_reward:.3f}")

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
print("🎯 STEP 6: Policy Reuse — Zero-Training Defense Deployment")
print("-" * 80)

from src.consumer.reuse import reuse_best_policy

# Get the training seed from the best policy's env_id
# Format: "cyber_defense_env_seed_{seed}_horizon_{time_horizon}"
best_agent_claim = next(c for c in claims if c.agent_id == best.agent_id)
env_parts = best_agent_claim.env_id.split("_")
training_seed = int(env_parts[env_parts.index("seed") + 1])

print(f"🔄 Reusing best policy from {best.agent_id} (trained on seed={training_seed})...")
print()

# Test 1: Same seed as training (demonstrates perfect reproducibility)
print("📊 Test 1: Same Environment (Deterministic Replay)")
print(f"   Using seed={training_seed} (same as training)")
reuse_start = time.time()
result_same = reuse_best_policy(best, seed=training_seed, episodes=100)
reuse_time_same = time.time() - reuse_start

print(f"   ✅ Reused Score: {result_same['policy_reward']:.3f}")
print(f"   📋 Verified Score: {result_same['verified_reward']:.3f}")
print(f"   📉 Baseline (random): {result_same['baseline_reward']:.3f}")
print(f"   📈 Improvement: {result_same['improvement']:+.1f}%")
print(f"   ⏱️  Time: {reuse_time_same:.2f}s")
print()

# Test 2: Different seed (demonstrates generalization limits)
print("📊 Test 2: Different Environment (Generalization)")
print(f"   Using seed=9999 (unseen attack patterns)")
reuse_start = time.time()
result_diff = reuse_best_policy(best, seed=9999, episodes=100)
reuse_time_diff = time.time() - reuse_start

print(f"   ✅ Reused Score: {result_diff['policy_reward']:.3f}")
print(f"   📉 Baseline (random): {result_diff['baseline_reward']:.3f}")
if result_diff['policy_reward'] > result_diff['baseline_reward']:
    print(f"   📈 Improvement: {result_diff['improvement']:+.1f}%")
else:
    print(f"   ⚠️  Score lower than baseline (policy trained on different patterns)")
print(f"   ⏱️  Time: {reuse_time_diff:.2f}s (instant deployment)")
print()

print("💡 Key Insights:")
print("   • Same seed: Perfect reproducibility (policy matches verification)")
print("   • Different seed: Shows generalization limits (expected for tabular Q-learning)")
print("   • Both: Instant deployment without retraining!")
print()

# Use same-seed result for final summary
result = result_same
reuse_time = reuse_time_same

# -----------------------------------------------------------------------------
# FINAL SUMMARY
# -----------------------------------------------------------------------------
total_time = time.time() - overall_start

print("=" * 80)
print("🎉 CYBER DEFENSE POLICY DEMO COMPLETE!")
print("=" * 80)
print()
print(f"⏱️  Total Demo Time: {total_time:.1f}s")
print()
print("✅ Complete Workflow:")
print(f"   • Training: {training_time:.1f}s ({len(claims)} agents)")
print(f"   • Verification: {verify_time:.1f}s ({valid_count} policies)")
print(f"   • Ledger: {recorded_count} entries recorded")
print(f"   • Marketplace: Best policy selected")
print(f"   • Reuse: {reuse_time:.2f}s (instant deployment!)")
print()
print("💡 This demonstrates:")
print("   • Decentralized learning (independent agents)")
print("   • Deterministic verification (replay guarantees)")
print("   • Tamper-evident ledger (hash-chained)")
print("   • Intelligent policy marketplace")
print("   • Zero-training policy reuse")
print(f"   • {result['improvement']:+.1f}% improvement over naive baseline")
print()
print("⚠️  DISCLAIMER:")
print("   This is a SIMULATED cyber defense environment for demonstrating")
print("   RL policy verification and reuse. NOT a real cybersecurity system.")
print()
print(f"📁 Ledger: {ledger_file}")
print(f"📁 Policies: policies/ directory")
print()
