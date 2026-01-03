"""
policy.py

Converts learned Q-table into shareable, verifiable policy artifacts.

Detailed description:
- Extracts deterministic policies from trained Q-tables
- Serializes policies for storage and transmission
- Generates cryptographic hashes for policy verification
- Provides complete policy lifecycle management

Main Components:
- extract_policy(): Converts Q-table to deterministic policy
- serialize_policy(): Converts policy to bytes for storage
- deserialize_policy(): Reconstructs policy from bytes
- hash_policy(): Generates SHA-256 fingerprint

Dependencies:
- json: For policy serialization
- hashlib: For cryptographic hashing

Author: PolicyLedger Team
Created: 2025-12-28
"""

from typing import Dict, Tuple
import json
import hashlib


# Type aliases for clarity
State = Tuple[int, int, int]  # (time_bucket, battery_bucket, demand)
Action = int  # 0=SAVE, 1=USE
Policy = Dict[State, Action]  # Deterministic mapping: state → best_action


def extract_policy(q_table: Dict[Tuple[State, Action], float]) -> Policy:
    """
    Extract deterministic policy from Q-table.

    For each state, pick the action with highest Q-value.

    Args:
        q_table: Trained Q-table {(state, action): q_value}

    Returns:
        Deterministic policy {state: best_action}

    Rules:
        - Does NOT include training metadata
        - Does NOT include rewards history
        - Pure state→action mapping
    """
    policy = {}

    # Get all unique states from Q-table
    states = set(state for (state, action) in q_table.keys())

    # For each state, find action with max Q-value
    for state in states:
        # Get Q-values for all actions in this state
        # Determine number of actions from Q-table
        available_actions = set(action for (s, action) in q_table.keys() if s == state)
        if not available_actions:
            # Fallback to common action space (cyber defense: 0-4)
            available_actions = [0, 1, 2, 3, 4]
        
        q_values = [(action, q_table.get((state, action), 0.0)) for action in available_actions]

        # Pick action with highest Q-value (deterministic)
        best_action = max(q_values, key=lambda x: x[1])[0]

        policy[state] = best_action

    return policy


def serialize_policy(policy: Policy) -> bytes:
    """
    Convert policy to bytes for storage/transmission.

    Fallback implementation using JSON serialization.
    (Google-first would use TensorFlow Lite format)

    Args:
        policy: Deterministic policy {state: action}

    Returns:
        Serialized policy as bytes

    Rules:
        - Does NOT depend on environment
        - Does NOT include randomness
        - Deterministic: same policy → same bytes
    """
    # Convert policy to JSON-serializable format
    # State tuples need to be converted to strings (JSON keys must be strings)
    serializable_policy = {
        str(state): action
        for state, action in policy.items()
    }

    # Serialize to JSON with sorted keys for determinism
    json_str = json.dumps(serializable_policy, sort_keys=True)

    # Convert to bytes
    return json_str.encode('utf-8')


def deserialize_policy(policy_bytes: bytes) -> Policy:
    """
    Convert bytes back to policy.

    Inverse of serialize_policy().

    Args:
        policy_bytes: Serialized policy

    Returns:
        Reconstructed policy {state: action}
    """
    # Decode bytes to JSON string
    json_str = policy_bytes.decode('utf-8')

    # Parse JSON
    serializable_policy = json.loads(json_str)

    # Convert string keys back to tuples
    policy = {}
    for state_str, action in serializable_policy.items():
        # Parse "(time_bucket, battery_bucket, demand)" → tuple
        state = eval(state_str)  # Safe here since we control the format
        policy[state] = action

    return policy


def hash_policy(policy_bytes: bytes) -> str:
    """
    Generate deterministic hash of policy artifact.

    This is the policy's fingerprint for verification.

    Args:
        policy_bytes: Serialized policy

    Returns:
        SHA-256 hash as hexadecimal string

    Rules:
        - Does NOT use timestamps
        - Does NOT include agent-specific noise
        - Pure hash: same bytes → same hash
    """
    return hashlib.sha256(policy_bytes).hexdigest()
