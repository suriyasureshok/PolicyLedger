"""
collector.py

Submission collector for managing policy claims before verification.

Detailed description:
- What problem this module solves: Provides a quarantine zone for collecting policy claims from agents before they are verified and stored in the ledger
- What it does NOT do: Does not perform verification, training, or policy execution; acts as a simple, dumb collection point
- Any assumptions or constraints: Accepts claims blindly without validation; relies on external verification for trust establishment

Main Components:
- Submission: Immutable record structure for policy claims with timestamps
- SubmissionCollector: Class for collecting, storing, and retrieving policy submissions
- submit(): Accepts and stores a new policy claim
- get_all_submissions(): Retrieves all collected submissions
- save_to_json(): Persists submissions to JSON file
- load_from_json(): Loads submissions from JSON file

Dependencies:
- typing: For type hints and annotations
- datetime: For timestamp generation
- json: For serialization and deserialization
- os: For file system operations
- src.agent.runner: For PolicyClaim structure

Author: Your Name
Created: 2025-12-28
"""

from typing import List, NamedTuple, Optional
from datetime import datetime
import json
import os
from src.agent.runner import PolicyClaim


class Submission(NamedTuple):
    """
    Immutable submission record with timestamp.

    Responsibilities:
    - Store policy claim with submission metadata
    - Provide unique identification for each submission
    - Preserve submission order and timing

    Attributes:
        claim (PolicyClaim): The policy claim submitted by an agent
        timestamp (str): ISO format timestamp of submission
        submission_id (int): Unique sequential identifier
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
    Blind submission collector for policy claims.

    Responsibilities:
    - Accept policy claims without validation or judgment
    - Preserve submission order and timestamps
    - Provide retrieval interfaces for collected submissions
    - Support persistence for fallback storage

    Attributes:
        _submissions (List[Submission]): Internal list of all submissions
        _next_id (int): Next available submission ID
    """
    
    def __init__(self):
        """
        Initialize empty submission collector.

        Sets up internal storage for submissions with no initial data.
        """
        self._submissions: List[Submission] = []
        self._next_id = 1
    
    def submit(self, claim: PolicyClaim) -> Submission:
        """
        Accept a policy claim submission.

        Args:
            claim (PolicyClaim): Policy claim from an agent

        Returns:
            Submission: Submission record with timestamp and unique ID
        """
        # Create submission record with timestamp and ID
        submission = Submission(
            claim=claim,
            timestamp=datetime.now().isoformat(),
            submission_id=self._next_id
        )
        
        # Store submission and increment ID counter
        self._submissions.append(submission)
        self._next_id += 1
        
        return submission
    
    def get_all_submissions(self) -> List[Submission]:
        """
        Get all submissions in order received.

        Returns:
            List[Submission]: Copy of all submissions in submission order
        """
        return self._submissions.copy()
    
    def get_submission_by_id(self, submission_id: int) -> Optional[Submission]:
        """
        Get specific submission by ID.

        Args:
            submission_id (int): Unique submission identifier

        Returns:
            Optional[Submission]: Submission if found, None otherwise
        """
        for submission in self._submissions:
            if submission.submission_id == submission_id:
                return submission
        return None
    
    def get_submissions_by_agent(self, agent_id: str) -> List[Submission]:
        """
        Get all submissions from specific agent.

        Args:
            agent_id (str): Agent identifier

        Returns:
            List[Submission]: All submissions from the specified agent
        """
        return [
            sub for sub in self._submissions
            if sub.claim.agent_id == agent_id
        ]
    
    def count_submissions(self) -> int:
        """
        Get total number of submissions.

        Returns:
            int: Total count of collected submissions
        """
        return len(self._submissions)
    
    def clear(self):
        """
        Clear all submissions.

        Warning:
            This should only be used for testing purposes.
        """
        self._submissions.clear()
        self._next_id = 1
    
    def save_to_json(self, filepath: str):
        """
        Save submissions to JSON file.

        Args:
            filepath (str): Path to JSON file for storage
        """
        submissions_data = []
        
        for sub in self._submissions:
            submissions_data.append({
                "submission_id": sub.submission_id,
                "timestamp": sub.timestamp,
                "agent_id": sub.claim.agent_id,
                "env_id": sub.claim.env_id,
                "policy_hash": sub.claim.policy_hash,
                "policy_artifact": sub.claim.policy_artifact.hex(),  # Serialize policy artifact to hex string for JSON compatibility
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
        Load submissions from JSON file.

        Args:
            filepath (str): Path to JSON file to load from

        Raises:
            FileNotFoundError: If the specified file does not exist
            JSONDecodeError: If the file contains invalid JSON
        """
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Clear current submissions before loading
        self._submissions.clear()
        
        # Restore from file
        max_id = 0
        for sub_data in data.get("submissions", []):
            # Reconstruct PolicyClaim from stored data
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
        
        # Update next ID to maintain uniqueness
        self._next_id = max_id + 1
    
    def __repr__(self) -> str:
        return (
            f"SubmissionCollector(\n"
            f"  total_submissions={len(self._submissions)},\n"
            f"  unique_agents={len(set(s.claim.agent_id for s in self._submissions))}\n"
            f")"
        )
