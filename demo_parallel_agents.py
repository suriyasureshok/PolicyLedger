"""
🚀 PARALLEL AGENT DEMO — 6 Agents Training Simultaneously 🎯

This demonstrates true decentralized learning:
    - 6 independent agents train in parallel (separate processes)
    - Each agent has its own environment instance
    - Each agent uses a different random seed
    - All agents train simultaneously (no coordination)
    - Results are collected and verified
    - Best policy is identified and reused

This is the CORE PROOF of decentralization.
"""

import multiprocessing as mp
from pathlib import Path
import json
import time
from typing import List, Tuple
from datetime import datetime
from src.agent.runner import run_agent, PolicyClaim

# -----------------------------------------------------------------------------
# Configuration - FAST DEMO VERSION
# -----------------------------------------------------------------------------

AGENT_CONFIGS = [
    ("agent_alpha", 42, 150),      # Seed 42, 150 episodes (FAST)
    ("agent_beta", 99, 150),       # Seed 99, 150 episodes (FAST)
    ("agent_gamma", 123, 150),     # Seed 123, 150 episodes (FAST)
    ("agent_delta", 256, 150),     # Seed 256, 150 episodes (FAST)
    ("agent_epsilon", 777, 150),   # Seed 777, 150 episodes (FAST)
    ("agent_zeta", 1024, 150),     # Seed 1024, 150 episodes (FAST)
]


# -----------------------------------------------------------------------------
# Worker Function (runs in separate process)
# -----------------------------------------------------------------------------

def train_agent_process(agent_id: str, seed: int, episodes: int, result_queue: mp.Queue):
    """
    Train a single agent in a separate process.
    
    Args:
        agent_id: Unique identifier for this agent
        seed: Random seed for environment
        episodes: Number of training episodes
        result_queue: Queue to put results into
    """
    try:
        start_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🤖 {agent_id} → Starting (seed={seed}, episodes={episodes})")
        
        # Train the agent
        claim = run_agent(agent_id, seed, episodes)
        
        elapsed = time.time() - start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {agent_id} → Done in {elapsed:.1f}s | Reward: {claim.claimed_reward:.3f}")
        
        # Convert claim to dict for serialization
        claim_dict = {
            'agent_id': claim.agent_id,
            'env_id': claim.env_id,
            'policy_hash': claim.policy_hash,
            'policy_artifact': claim.policy_artifact.hex(),  # Convert bytes to hex string
            'claimed_reward': claim.claimed_reward,
            'training_time': elapsed
        }
        
        result_queue.put(('success', claim_dict))
        
    except Exception as e:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ {agent_id} → FAILED: {str(e)}")
        result_queue.put(('error', {'agent_id': agent_id, 'error': str(e)}))


# -----------------------------------------------------------------------------
# Main Demo
# -----------------------------------------------------------------------------

def main():
    overall_start = time.time()
    
    print("=" * 80)
    print("🚀 PARALLEL AGENT DEMO — 6 AGENTS TRAINING SIMULTANEOUSLY 🎯")
    print("=" * 80)
    print()
    print("⚡ FAST DEMO MODE: 150 episodes per agent")
    print()
    print("This demonstrates true decentralized learning:")
    print("  • 6 independent agents train in parallel")
    print("  • Each agent has its own environment instance")
    print("  • Each agent uses a different random seed")
    print("  • All agents train simultaneously (no coordination)")
    print()
    print("=" * 80)
    print()
    
    # -----------------------------------------------------------------------------
    # STEP 1: Launch All Agents in Parallel
    # -----------------------------------------------------------------------------
    print("📚 STEP 1: Launch All Agents in Parallel")
    print("-" * 80)
    
    # Create a queue for collecting results
    result_queue = mp.Queue()
    
    # Launch all agents as separate processes
    processes = []
    launch_start = time.time()
    
    for agent_id, seed, episodes in AGENT_CONFIGS:
        process = mp.Process(
            target=train_agent_process,
            args=(agent_id, seed, episodes, result_queue),
            daemon=False
        )
        process.start()
        processes.append((agent_id, process))
    
    print(f"🚀 Launched {len(processes)} parallel processes")
    print(f"⏳ Training in progress...\n")
    
    # Wait for all processes with timeout
    all_done = True
    for agent_id, process in processes:
        process.join(timeout=120)  # 2 minute timeout per agent
        if process.is_alive():
            print(f"⚠️  {agent_id} timed out, terminating...")
            process.terminate()
            all_done = False
    
    training_time = time.time() - launch_start
    
    print(f"\n{'=' * 80}")
    print(f"✅ All agents completed in {training_time:.1f} seconds")
    print("=" * 80)
    print()
    
    # -----------------------------------------------------------------------------
    # STEP 2: Collect Results
    # -----------------------------------------------------------------------------
    print("📊 STEP 2: Collect Training Results")
    print("-" * 80)
    
    claims = []
    errors = []
    total_training_time = 0
    
    # Collect all results from queue
    while not result_queue.empty():
        status, data = result_queue.get()
        if status == 'success':
            # Reconstruct PolicyClaim from dict
            claim = PolicyClaim(
                agent_id=data['agent_id'],
                env_id=data['env_id'],
                policy_hash=data['policy_hash'],
                policy_artifact=bytes.fromhex(data['policy_artifact']),
                claimed_reward=data['claimed_reward']
            )
            claims.append(claim)
            total_training_time += data.get('training_time', 0)
        else:
            errors.append(data)
    
    print(f"✅ Successfully trained: {len(claims)}/{len(AGENT_CONFIGS)} agents")
    print(f"⏱️  Total training time (sequential would be): {total_training_time:.1f}s")
    print(f"🚀 Parallel speedup: {total_training_time/training_time:.1f}x faster!")
    
    if errors:
        print(f"\n❌ Failed: {len(errors)} agents")
        for error in errors:
            print(f"   • {error['agent_id']}: {error['error']}")
    
    print()
    
    # Display results
    print("Training Results (sorted by reward):")
    print("-" * 80)
    claims_sorted = sorted(claims, key=lambda c: c.claimed_reward, reverse=True)
    for i, claim in enumerate(claims_sorted, 1):
        bar = "█" * int(claim.claimed_reward * 10)
        print(f"  {i}. {claim.agent_id:15s} → {claim.claimed_reward:7.3f} {bar}")
    print()
    
    if not claims:
        print("❌ No successful training results. Exiting.")
        return
    
    # -----------------------------------------------------------------------------
    # STEP 3: Verify All Claims (FAST)
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
        print(f"{status_icon} {claim.agent_id:15s} → {result.verified_reward:.3f}")
    
    verify_time = time.time() - verify_start
    valid_count = sum(1 for r in verified_results if r.status.value == "VALID")
    print(f"\n✅ Verified {valid_count}/{len(claims)} policies in {verify_time:.1f}s")
    print()
    
    # -----------------------------------------------------------------------------
    # STEP 4: Record in Ledger (FAST)
    # -----------------------------------------------------------------------------
    print("=" * 80)
    print("📝 STEP 4: Record Verified Policies in Ledger")
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
    
    print(f"✅ Recorded {recorded_count} verified policies")
    
    # Verify chain integrity
    entries = ledger.read_all()
    is_intact = verify_chain_integrity(entries)
    print(f"🔗 Hash chain: {'✅ INTACT' if is_intact else '❌ BROKEN'}")
    print()
    
    # -----------------------------------------------------------------------------
    # STEP 5: Marketplace Selection (INSTANT)
    # -----------------------------------------------------------------------------
    print("=" * 80)
    print("🏆 STEP 5: Marketplace Selects Best Policy")
    print("-" * 80)
    
    from src.marketplace.ranking import select_best_policy
    
    best = select_best_policy(ledger)
    
    if best:
        print(f"🏆 WINNER: {best.agent_id}")
        print(f"   Reward: {best.verified_reward:.3f}")
        print(f"   Hash: {best.policy_hash[:16]}...")
    else:
        print("❌ No valid policies found")
        return
    print()
    
    # -----------------------------------------------------------------------------
    # STEP 6: Policy Reuse - THE WOW MOMENT (INSTANT)
    # -----------------------------------------------------------------------------
    print("=" * 80)
    print("🎯 STEP 6: Policy Reuse — THE WOW MOMENT")
    print("-" * 80)
    
    from src.consumer.reuse import reuse_best_policy
    
    print("🔄 Consumer reusing best policy (NO TRAINING)...")
    reuse_start = time.time()
    result = reuse_best_policy(ledger, env_seed=9999)
    reuse_time = time.time() - reuse_start
    
    print(f"\n✅ Policy Reuse Complete in {reuse_time:.2f}s!")
    print(f"   Best Policy: {result.best_policy.agent_id}")
    print(f"   Verified: {result.best_policy.verified_reward:.3f}")
    print(f"   Reused: {result.reuse_reward:.3f}")
    print(f"   Baseline: {result.baseline_reward:.3f}")
    print(f"   Improvement: {result.improvement_vs_baseline:+.1f}%")
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
    print("✅ Key Achievements:")
    print(f"   • {len(claims)} agents trained in parallel ({training_time:.1f}s)")
    print(f"   • {total_training_time/training_time:.1f}x speedup from parallelization")
    print(f"   • {valid_count} policies verified ({verify_time:.1f}s)")
    print(f"   • {recorded_count} policies recorded in tamper-evident ledger")
    print(f"   • Best policy reused instantly ({reuse_time:.2f}s)")
    print(f"   • {result.improvement_vs_baseline:+.1f}% improvement over random baseline")
    print()
    print("💡 This demonstrates:")
    print("   • True decentralized learning (parallel agents)")
    print("   • Deterministic verification")
    print("   • Tamper-evident ledger")
    print("   • Intelligent policy marketplace")
    print("   • Zero-training policy reuse")
    print()
    print(f"📁 Ledger saved to: {ledger_file}")
    print()


if __name__ == "__main__":
    # Required for Windows multiprocessing
    mp.freeze_support()
    main()
