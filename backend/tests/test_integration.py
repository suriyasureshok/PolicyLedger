"""
End-to-End Integration Test: Training → Submission → Verification

This test demonstrates the complete PolicyLedger workflow for Phase 7.
"""

from src.agent.runner import run_agent
from src.submission.collector import SubmissionCollector
from src.verifier.verifier import PolicyVerifier, VerificationStatus


def test_complete_workflow():
    """
    Test the complete workflow from training to verification.
    
    Steps:
    1. Agent trains policy
    2. Agent submits claim
    3. Verifier verifies claim
    4. Result is binary and explainable
    """
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Complete Workflow")
    print("=" * 70 + "\n")
    
    # Step 1: Train agent
    print("Step 1: Training agent...")
    claim = run_agent(agent_id="integration_test_agent", seed=42, episodes=500)
    print(f"✅ Agent trained")
    print(f"   Claimed reward: {claim.claimed_reward:.3f}")
    print(f"   Policy hash: {claim.policy_hash[:16]}...")
    print()
    
    # Step 2: Submit claim
    print("Step 2: Submitting claim...")
    collector = SubmissionCollector()
    submission = collector.submit(claim)
    print(f"✅ Claim submitted")
    print(f"   Submission ID: {submission.submission_id}")
    print(f"   Timestamp: {submission.timestamp}")
    print()
    
    # Step 3: Verify claim
    print("Step 3: Verifying claim through deterministic replay...")
    verifier = PolicyVerifier(reward_threshold=1e-6)
    result = verifier.verify(claim)
    print(f"✅ Verification complete")
    print(f"   Status: {result.status.value}")
    print(f"   Verified reward: {result.verified_reward:.3f}")
    print(f"   Reason: {result.reason}")
    print()
    
    # Step 4: Validate results
    print("Step 4: Validating results...")
    assert result.status == VerificationStatus.VALID, "Integration test should pass"
    assert result.verified_reward is not None, "Verified reward should exist"
    assert abs(result.verified_reward - claim.claimed_reward) < 1e-6, "Rewards should match"
    print("✅ All validations passed")
    print()
    
    print("=" * 70)
    print("INTEGRATION TEST PASSED ✅")
    print("=" * 70)
    print()
    print("Workflow validated:")
    print("  1. Agent trains → claims reward")
    print("  2. Submission accepted → timestamped")
    print("  3. Verifier replays → confirms reward")
    print("  4. Binary decision → explainable result")
    print()
    print("Ready for:")
    print("  → Phase 8: Ledger (immutable storage)")
    print("  → Phase 9: Marketplace (ranking)")
    print("  → Phase 10: Policy Reuse (the wow moment)")
    print()


if __name__ == "__main__":
    test_complete_workflow()
