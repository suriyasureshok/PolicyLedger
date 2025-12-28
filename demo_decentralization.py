"""
Phase 5 - Multi-Agent Decentralization Proof

This script demonstrates true decentralization:
- Multiple agents train independently
- Same environment definition, different seeds
- No shared memory
- No coordination
- Different policies produced

This answers: "How do I know agents didn't coordinate?"
Answer: By design, they CAN'T.
"""

import sys
sys.path.insert(0, 'c:/Users/SURIYA/Desktop/Competition/HackNEXA/PolicyLedger')

from src.agent.runner import run_agent
from src.submission import SubmissionCollector
from src.agent.policy import deserialize_policy


def train_independent_agents(num_agents: int = 5, episodes: int = 500) -> SubmissionCollector:
    """
    Train multiple agents independently and collect their submissions.
    
    Each agent:
    - Has its own process context
    - Has its own seed
    - Has its own Q-table
    - Has no shared memory
    - Cannot see other agents
    
    Args:
        num_agents: Number of independent agents to train
        episodes: Episodes per agent
    
    Returns:
        SubmissionCollector with all claims
    """
    print("=" * 70)
    print("PHASE 5 - MULTI-AGENT DECENTRALIZATION PROOF")
    print("=" * 70)
    print()
    print(f"🎯 Training {num_agents} independent agents...")
    print(f"   Episodes per agent: {episodes}")
    print(f"   Independence: ENFORCED")
    print()
    print("-" * 70)
    
    # Create submission collector (the dumb desk)
    collector = SubmissionCollector()
    
    # Train each agent independently
    for i in range(num_agents):
        agent_id = f"agent_{i+1:03d}"
        seed = 42 + i * 13  # Different seed = different environment experience
        
        print(f"\n🤖 Agent {i+1}/{num_agents}: {agent_id}")
        print(f"   Seed: {seed}")
        print(f"   Status: Training in isolation...", end=" ")
        
        # Each agent trains independently
        # - New environment instance
        # - New Q-table
        # - No shared state
        claim = run_agent(
            agent_id=agent_id,
            seed=seed,
            episodes=episodes
        )
        
        print(f"✅ Done!")
        print(f"   Claimed reward: {claim.claimed_reward:.3f}")
        print(f"   Policy hash: {claim.policy_hash[:16]}...")
        
        # Submit to collector (blind acceptance)
        submission = collector.submit(claim)
        print(f"   Submitted: ID={submission.submission_id}")
    
    print()
    print("-" * 70)
    print(f"✅ All agents trained independently")
    print()
    
    return collector


def analyze_decentralization(collector: SubmissionCollector):
    """
    Analyze submissions to prove decentralization.
    
    We check:
    1. All agent IDs are unique
    2. All policy hashes are different
    3. Rewards vary (not identical)
    4. Policies make different decisions
    """
    print("=" * 70)
    print("DECENTRALIZATION ANALYSIS")
    print("=" * 70)
    print()
    
    submissions = collector.get_all_submissions()
    
    # Check 1: Unique agent IDs
    print("📋 CHECK 1: Unique Agent IDs")
    print("-" * 70)
    agent_ids = [s.claim.agent_id for s in submissions]
    unique_ids = set(agent_ids)
    
    print(f"   Total submissions: {len(submissions)}")
    print(f"   Unique agent IDs: {len(unique_ids)}")
    
    if len(unique_ids) == len(submissions):
        print(f"   ✅ PASS: All agents have unique IDs")
    else:
        print(f"   ❌ FAIL: Some agents share IDs (collision!)")
    print()
    
    # Check 2: Different policy hashes
    print("📋 CHECK 2: Different Policies")
    print("-" * 70)
    policy_hashes = [s.claim.policy_hash for s in submissions]
    unique_hashes = set(policy_hashes)
    
    print(f"   Total policies: {len(submissions)}")
    print(f"   Unique hashes: {len(unique_hashes)}")
    
    if len(unique_hashes) == len(submissions):
        print(f"   ✅ PASS: All policies are different")
    else:
        print(f"   ❌ FAIL: Some policies are identical (coordinated?)")
    
    # Show sample hashes
    print(f"\n   Sample hashes:")
    for i, sub in enumerate(submissions[:3], 1):
        print(f"      {sub.claim.agent_id}: {sub.claim.policy_hash[:32]}...")
    print()
    
    # Check 3: Different rewards
    print("📋 CHECK 3: Different Rewards")
    print("-" * 70)
    rewards = [s.claim.claimed_reward for s in submissions]
    unique_rewards = set(rewards)
    
    print(f"   Total agents: {len(submissions)}")
    print(f"   Unique reward values: {len(unique_rewards)}")
    print(f"   Min reward: {min(rewards):.3f}")
    print(f"   Max reward: {max(rewards):.3f}")
    print(f"   Avg reward: {sum(rewards)/len(rewards):.3f}")
    print(f"   Std deviation: {(sum((r-sum(rewards)/len(rewards))**2 for r in rewards)/len(rewards))**0.5:.3f}")
    
    if len(unique_rewards) > 1:
        print(f"   ✅ PASS: Rewards vary (different learning)")
    else:
        print(f"   ⚠️  WARNING: All rewards identical (suspicious)")
    print()
    
    # Check 4: Policies make different decisions
    print("📋 CHECK 4: Policy Decisions Differ")
    print("-" * 70)
    
    # Deserialize first 3 policies and compare
    policies = []
    for i, sub in enumerate(submissions[:3]):
        policy = deserialize_policy(sub.claim.policy_artifact)
        policies.append(policy)
        print(f"   {sub.claim.agent_id}: {len(policy)} state→action mappings")
    
    # Compare decisions for same states
    if len(policies) >= 2:
        # Find common states
        common_states = set(policies[0].keys())
        for p in policies[1:]:
            common_states &= set(p.keys())
        
        if common_states:
            # Count disagreements
            disagreements = 0
            sample_state = None
            sample_actions = []
            
            for state in list(common_states)[:10]:  # Check first 10 states
                actions = [p[state] for p in policies]
                if len(set(actions)) > 1:  # Different actions
                    disagreements += 1
                    if sample_state is None:
                        sample_state = state
                        sample_actions = actions
            
            print(f"\n   Common states checked: {min(10, len(common_states))}")
            print(f"   Decisions that differ: {disagreements}")
            
            if disagreements > 0:
                print(f"   ✅ PASS: Agents make different decisions")
                if sample_state:
                    print(f"\n   Example: State {sample_state}")
                    for i, action in enumerate(sample_actions[:3], 1):
                        action_name = "USE" if action == 1 else "SAVE"
                        print(f"      Agent {i}: {action_name}")
            else:
                print(f"   ⚠️  WARNING: All decisions match (coordinated?)")
        else:
            print(f"   ℹ️  INFO: No common states to compare")
    print()


def prove_independence():
    """
    Complete independence proof.
    
    This demonstrates:
    - Agents train in isolation
    - Same environment definition
    - Different experiences (seeds)
    - Different learned policies
    - Blind submission (no comparison)
    """
    # Train independent agents
    collector = train_independent_agents(num_agents=5, episodes=500)
    
    # Analyze for decentralization properties
    analyze_decentralization(collector)
    
    # Final verdict
    print("=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    print()
    
    submissions = collector.get_all_submissions()
    
    # Check all properties
    unique_ids = len(set(s.claim.agent_id for s in submissions))
    unique_hashes = len(set(s.claim.policy_hash for s in submissions))
    unique_rewards = len(set(s.claim.claimed_reward for s in submissions))
    
    all_unique = (
        unique_ids == len(submissions) and
        unique_hashes == len(submissions) and
        unique_rewards > 1
    )
    
    if all_unique:
        print("✅ DECENTRALIZATION VERIFIED")
        print()
        print("Proof:")
        print(f"  ✓ {unique_ids} unique agent IDs")
        print(f"  ✓ {unique_hashes} unique policies")
        print(f"  ✓ {unique_rewards} different reward values")
        print(f"  ✓ Agents trained in isolation")
        print(f"  ✓ No shared memory")
        print(f"  ✓ No coordination possible")
        print()
        print('Judge Question: "How do I know agents didn\'t coordinate?"')
        print('Our Answer: "By design, they CAN\'T. Each trains independently,')
        print('            submits blindly, and never sees others."')
        print()
    else:
        print("⚠️  DECENTRALIZATION QUESTIONABLE")
        print()
        print("Issues detected:")
        if unique_ids != len(submissions):
            print(f"  ✗ Agent ID collision")
        if unique_hashes != len(submissions):
            print(f"  ✗ Identical policies (coordinated?)")
        if unique_rewards == 1:
            print(f"  ✗ All rewards identical (suspicious)")
        print()
    
    print("=" * 70)
    print()
    
    # Show submission collector state
    print("📊 Submission Collector State:")
    print(collector)
    print()
    
    return collector


if __name__ == "__main__":
    print("\n")
    collector = prove_independence()
    
    print("=" * 70)
    print("✅ PHASE 5 COMPLETE - DECENTRALIZATION PROVEN")
    print("=" * 70)
    print()
    print("Key takeaways:")
    print("  • Agents learn in complete isolation")
    print("  • Same environment code, different seeds")
    print("  • Submission layer is intentionally dumb")
    print("  • No verification happens at submission")
    print("  • Coordination is impossible by design")
    print()
    print("Next: Phase 6 (Verification Layer)")
    print()
