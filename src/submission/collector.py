"""
Submission Collector - Intentionally Dumb

This is the quarantine zone between learning and trust.
Accepts claims blindly. Does nothing smart.
"""

from typing import List, NamedTuple, Optional
from datetime import datetime
import json
import os
from src.agent.runner import PolicyClaim


class Submission(NamedTuple):
    """
    Submission record with timestamp.
    
    This is what gets stored when an agent submits.
    """
    claim: PolicyClaim
    timestamp: str
    submission_id: int
    
    def __repr__(self) -> str:
        return (
            f"Submission(\n"
            f"  id={self.submission_id},\n"
            f"  agent={self.claim.agent_id},\n"
            f"  reward={self.claim.claimed_reward:.3f},\n"
            f"  hash={self.claim.policy_hash[:16]}...,\n"
            f"  timestamp={self.timestamp}\n"
            f")"
        )


class SubmissionCollector:
    """
    Blind submission collector.
    
    This is the exam submission desk. It:
    - Accepts any claim
    - Preserves order
    - Records timestamp
    - Does NOTHING else
    
    Rules:
    - Does NOT verify rewards
    - Does NOT compare agents
    - Does NOT reject claims
    - Does NOT modify artifacts
    - Does NOT decide trust
    
    Metaphor: This is where students drop their answer sheets.
              No grading happens here.
    """
    
    def __init__(self):
        """Initialize empty submission queue."""
        self._submissions: List[Submission] = []
        self._next_id = 1
    
    def submit(self, claim: PolicyClaim) -> Submission:
        """
        Accept a policy claim submission.
        
        This is intentionally dumb. No validation, no judgment.
        
        Args:
            claim: PolicyClaim from an agent
        
        Returns:
            Submission record with timestamp and ID
        
        Rules:
            - Does NOT check if reward is valid
            - Does NOT check if policy makes sense
            - Does NOT compare with other submissions
            - Just accepts and stores
        """
        # Create submission record
        submission = Submission(
            claim=claim,
            timestamp=datetime.now().isoformat(),
            submission_id=self._next_id
        )
        
        # Store it
        self._submissions.append(submission)
        self._next_id += 1
        
        return submission
    
    def get_all_submissions(self) -> List[Submission]:
        """
        Get all submissions in order received.
        
        Returns:
            List of all submissions
        """
        return self._submissions.copy()
    
    def get_submission_by_id(self, submission_id: int) -> Optional[Submission]:
        """
        Get specific submission by ID.
        
        Args:
            submission_id: Submission ID
        
        Returns:
            Submission if found, None otherwise
        """
        for submission in self._submissions:
            if submission.submission_id == submission_id:
                return submission
        return None
    
    def get_submissions_by_agent(self, agent_id: str) -> List[Submission]:
        """
        Get all submissions from specific agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            List of submissions from this agent
        """
        return [
            sub for sub in self._submissions
            if sub.claim.agent_id == agent_id
        ]
    
    def count_submissions(self) -> int:
        """Get total number of submissions."""
        return len(self._submissions)
    
    def clear(self):
        """
        Clear all submissions (for testing only).
        
        WARNING: This should NEVER be used in demo or production pipeline.
        """
        self._submissions.clear()
        self._next_id = 1
    
    def save_to_json(self, filepath: str):
        """
        Save submissions to JSON file (fallback persistence).
        
        This provides local fallback storage before Firebase integration.
        
        Args:
            filepath: Path to JSON file
        
        Rules:
            - Does NOT modify submissions
            - Does NOT filter or validate
            - Just serializes verbatim
        """
        submissions_data = []
        
        for sub in self._submissions:
            submissions_data.append({
                "submission_id": sub.submission_id,
                "timestamp": sub.timestamp,
                "agent_id": sub.claim.agent_id,
                "env_id": sub.claim.env_id,
                "policy_hash": sub.claim.policy_hash,
                "policy_artifact": sub.claim.policy_artifact.hex(),  # Convert bytes to hex
                "claimed_reward": sub.claim.claimed_reward
            })
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump({
                "total_submissions": len(submissions_data),
                "submissions": submissions_data
            }, f, indent=2)
    
    def load_from_json(self, filepath: str):
        """
        Load submissions from JSON file (fallback persistence).
        
        Args:
            filepath: Path to JSON file
        
        Rules:
            - Restores exact submission order
            - Does NOT validate loaded data
            - Trusts file content blindly
        """
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Clear current submissions
        self._submissions.clear()
        
        # Restore from file
        max_id = 0
        for sub_data in data.get("submissions", []):
            # Reconstruct PolicyClaim
            claim = PolicyClaim(
                agent_id=sub_data["agent_id"],
                env_id=sub_data["env_id"],
                policy_hash=sub_data["policy_hash"],
                policy_artifact=bytes.fromhex(sub_data["policy_artifact"]),
                claimed_reward=sub_data["claimed_reward"]
            )
            
            # Reconstruct Submission
            submission = Submission(
                claim=claim,
                timestamp=sub_data["timestamp"],
                submission_id=sub_data["submission_id"]
            )
            
            self._submissions.append(submission)
            max_id = max(max_id, sub_data["submission_id"])
        
        # Update next ID
        self._next_id = max_id + 1
    
    def __repr__(self) -> str:
        return (
            f"SubmissionCollector(\n"
            f"  total_submissions={len(self._submissions)},\n"
            f"  unique_agents={len(set(s.claim.agent_id for s in self._submissions))}\n"
            f")"
        )
