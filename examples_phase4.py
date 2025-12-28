"""
Phase 4 Examples - RL Agent Usage Patterns

This script demonstrates various ways to use the RL agent module.
"""

import sys
sys.path.insert(0, 'c:/Users/SURIYA/Desktop/Competition/HackNEXA/PolicyLedger')

from src.agent import run_agent, quick_train, PolicyClaim
from src.agent.policy import deserialize_policy
from src.shared.env import EnergySlotEnv


def example_1_basic_training():
    """Example 1: Basic agent training."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Agent Training")
    print("=" * 60)
    print()
    
    # Quick training with defaults
    claim = quick_train(agent_id="agent_001", seed=42, episodes=500)
    
    print(f"✅ Agent trained successfully!")
    print(f"   Agent ID: {claim.agent_id}")
    print(f"   Environment: {claim.env_id}")
    print(f"   Claimed Reward: {claim.claimed_reward:.3f}")
    print(f"   Policy Hash: {claim.policy_hash[:32]}...")
    print()


def example_2_custom_parameters():
    """Example 2: Training with custom parameters."""
    print("=" * 60)
    print("EXAMPLE 2: Custom Training Parameters")
    print("=" * 60)
    print()
    
    # Custom training configuration
    claim = run_agent(
        agent_id="agent_custom",
        seed=123,
        episodes=2000,           # More training
        time_slots=48,           # Longer horizon
        battery_capacity=2.0,    # Larger battery
        energy_cost=0.05         # Lower cost per use
    )
    
    print(f"✅ Custom training complete!")
    print(f"   Episodes: 2000")
    print(f"   Time Slots: 48")
    print(f"   Claimed Reward: {claim.claimed_reward:.3f}")
    print()


def example_3_policy_inspection():
    """Example 3: Inspecting the learned policy."""
    print("=" * 60)
    print("EXAMPLE 3: Policy Inspection")
    print("=" * 60)
    print()
    
    # Train agent
    claim = quick_train(agent_id="agent_inspect", seed=99, episodes=500)
    
    # Deserialize and inspect policy
    policy = deserialize_policy(claim.policy_artifact)
    
    print(f"📊 Policy Statistics:")
    print(f"   Total states: {len(policy)}")
    print()
    
    # Count actions
    save_count = sum(1 for action in policy.values() if action == 0)
    use_count = sum(1 for action in policy.values() if action == 1)
    
    print(f"   Action Distribution:")
    print(f"      SAVE: {save_count} states ({save_count/len(policy)*100:.1f}%)")
    print(f"      USE:  {use_count} states ({use_count/len(policy)*100:.1f}%)")
    print()
    
    # Show policy decisions by demand
    print(f"   Policy by Demand:")
    demand_0_use = sum(1 for (tb, bb, d), a in policy.items() if d == 0 and a == 1)
    demand_0_total = sum(1 for (tb, bb, d), a in policy.items() if d == 0)
    demand_1_use = sum(1 for (tb, bb, d), a in policy.items() if d == 1 and a == 1)
    demand_1_total = sum(1 for (tb, bb, d), a in policy.items() if d == 1)
    
    if demand_0_total > 0:
        print(f"      When demand=0: USE {demand_0_use}/{demand_0_total} times ({demand_0_use/demand_0_total*100:.1f}%)")
    if demand_1_total > 0:
        print(f"      When demand=1: USE {demand_1_use}/{demand_1_total} times ({demand_1_use/demand_1_total*100:.1f}%)")
    print()


def example_4_decentralized_agents():
    """Example 4: Multiple independent agents (decentralized learning)."""
    print("=" * 60)
    print("EXAMPLE 4: Decentralized Multi-Agent Learning")
    print("=" * 60)
    print()
    
    print("🌐 Training 5 independent agents...")
    print()
    
    agents = []
    for i in range(5):
        agent_id = f"agent_{i+1:03d}"
        seed = 42 + i * 7  # Different environment for each
        
        claim = quick_train(agent_id=agent_id, seed=seed, episodes=400)
        agents.append(claim)
        
        print(f"  ✅ {agent_id}: reward={claim.claimed_reward:6.3f}, hash={claim.policy_hash[:12]}...")
    
    print()
    print(f"📊 Results:")
    print(f"   Total agents: {len(agents)}")
    print(f"   Unique policies: {len(set(c.policy_hash for c in agents))}")
    print(f"   Avg reward: {sum(c.claimed_reward for c in agents)/len(agents):.3f}")
    print(f"   Best reward: {max(c.claimed_reward for c in agents):.3f}")
    print(f"   Worst reward: {min(c.claimed_reward for c in agents):.3f}")
    print()


def example_5_determinism_verification():
    """Example 5: Verify deterministic training."""
    print("=" * 60)
    print("EXAMPLE 5: Determinism Verification")
    print("=" * 60)
    print()
    
    print("🔍 Training same agent twice with same seed...")
    print()
    
    # Train twice with same parameters
    claim1 = quick_train(agent_id="agent_det1", seed=777, episodes=300)
    claim2 = quick_train(agent_id="agent_det2", seed=777, episodes=300)
    
    print(f"  Agent 1: hash={claim1.policy_hash[:16]}..., reward={claim1.claimed_reward:.3f}")
    print(f"  Agent 2: hash={claim2.policy_hash[:16]}..., reward={claim2.claimed_reward:.3f}")
    print()
    
    if claim1.policy_hash == claim2.policy_hash:
        print("✅ DETERMINISTIC: Same seed → Same policy hash")
    else:
        print("❌ WARNING: Policies differ despite same seed!")
    
    if abs(claim1.claimed_reward - claim2.claimed_reward) < 0.001:
        print("✅ DETERMINISTIC: Same seed → Same reward")
    else:
        print("❌ WARNING: Rewards differ despite same seed!")
    
    print()


def example_6_policy_artifact_size():
    """Example 6: Analyze policy artifact properties."""
    print("=" * 60)
    print("EXAMPLE 6: Policy Artifact Analysis")
    print("=" * 60)
    print()
    
    # Train agent
    claim = quick_train(agent_id="agent_artifact", seed=555, episodes=500)
    
    # Analyze artifact
    artifact_size = len(claim.policy_artifact)
    hash_size = len(claim.policy_hash)
    
    print(f"📦 Artifact Properties:")
    print(f"   Policy artifact size: {artifact_size} bytes ({artifact_size/1024:.2f} KB)")
    print(f"   Policy hash size: {hash_size} characters")
    print(f"   Hash algorithm: SHA-256")
    print()
    
    # Verify hash
    from src.agent.policy import hash_policy
    recomputed_hash = hash_policy(claim.policy_artifact)
    
    if recomputed_hash == claim.policy_hash:
        print("✅ Hash verification: PASSED")
    else:
        print("❌ Hash verification: FAILED")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "PHASE 4 - RL AGENT EXAMPLES" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    examples = [
        example_1_basic_training,
        example_2_custom_parameters,
        example_3_policy_inspection,
        example_4_decentralized_agents,
        example_5_determinism_verification,
        example_6_policy_artifact_size,
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
        except Exception as e:
            print(f"❌ Example {i} failed: {e}")
            import traceback
            traceback.print_exc()
        
        if i < len(examples):
            input("Press Enter to continue to next example...")
            print("\n")
    
    print("=" * 60)
    print("✅ ALL EXAMPLES COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
