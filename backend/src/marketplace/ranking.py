"""
ranking.py

Policy marketplace for selecting and ranking verified policies.

Detailed description:
- What problem this module solves: Provides deterministic selection and ranking of verified policies from the ledger for marketplace operations
- What it does NOT do: Does not perform policy verification, training, or storage; focuses solely on selection and ranking logic
- Any assumptions or constraints: Assumes ledger contains only verified policies; ranking is based on verified rewards with tie-breaking by timestamp

Main Components:
- BestPolicyReference: Immutable reference structure for the best policy
- PolicyMarketplace: Class for marketplace operations and policy ranking
- get_best_policy(): Retrieves the highest-performing verified policy
- get_ranked_policies(): Returns a ranked list of all verified policies
- select_best_policy(): Convenience function for selecting the best policy

Dependencies:
- typing: For type hints and annotations
- src.ledger.ledger: For LedgerEntry and PolicyLedger classes

Author: Your Name
Created: 2025-12-28
"""

from typing import Optional, NamedTuple, List
from src.ledger.ledger import LedgerEntry, PolicyLedger


class BestPolicyReference(NamedTuple):
    """
    Immutable reference to the best verified policy.

    Serves as a pointer to the highest-performing verified policy without
    containing the policy artifact itself. Enables decoupling of selection
    from storage and execution.

    Attributes:
        policy_hash: SHA-256 hash of the selected policy artifact
        verified_reward: Performance metric confirmed by verification layer
        agent_id: Unique identifier of the agent that created the policy
    """
    policy_hash: str
    verified_reward: float
    agent_id: str


class PolicyMarketplace:
    """
    Deterministic policy selection based on verified performance metrics.

    Implements marketplace functionality as a pure function over
    the ledger. Selects the highest-performing verified policy using
    deterministic ranking rules with tie-breaking.

    Core Responsibilities:
        - Read verified policy entries from ledger (trusted input)
        - Rank policies by verified_reward (highest first)
        - Apply timestamp tie-breaking for deterministic selection
        - Return immutable policy references for reuse

    Design Principles:
        - Pure function: Same ledger state → same selection result
        - No side effects: Does not modify ledger or policies
        - Deterministic: Timestamp tie-breaking ensures consistent results
        - Trusting: Assumes ledger entries are already verified

    Attributes:
        ledger: PolicyLedger instance providing verified entries
    """

    def __init__(self, ledger: PolicyLedger):
        """
        Initialize marketplace with ledger access.

        Args:
            ledger: PolicyLedger instance containing verified policy entries
        """
        self.ledger = ledger
    
    def get_best_policy(self) -> Optional[BestPolicyReference]:
        """
        Select the highest-performing verified policy.

        Implements deterministic selection algorithm:
        1. Primary sort: Highest verified_reward wins
        2. Tie-breaking: Earlier timestamp wins (deterministic)

        Returns:
            BestPolicyReference to highest-performing policy, or None if
            ledger is empty

        Note:
            Selection is deterministic and reproducible. Same ledger state
            will always return the same result.
        """
        # Read all verified entries
        entries = self.ledger.read_all()
        
        # Edge case: Empty ledger
        if not entries:
            return None
        
        # Edge case: Single entry (best by definition)
        if len(entries) == 1:
            entry = entries[0]
            return BestPolicyReference(
                policy_hash=entry.policy_hash,
                verified_reward=entry.verified_reward,
                agent_id=entry.agent_id
            )
        
        # Multiple entries: Rank by verified_reward (descending), then timestamp (ascending)
        # Sorting criteria:
        #   Primary: Higher reward wins (use negated for min-to-max comparison)
        #   Secondary: Earlier timestamp wins (string comparison works for ISO format)
        best_entry = min(
            entries,
            key=lambda e: (-e.verified_reward, e.timestamp)  # Higher reward first, earlier time first
        )
        
        return BestPolicyReference(
            policy_hash=best_entry.policy_hash,
            verified_reward=best_entry.verified_reward,
            agent_id=best_entry.agent_id
        )
    
    def get_ranked_policies(self) -> List[BestPolicyReference]:
        """
        Get all verified policies ranked by performance.

        Returns complete ranking of all verified policies in the ledger,
        sorted by the same deterministic rules as get_best_policy().

        Returns:
            List of BestPolicyReference objects sorted by:
            1. verified_reward (descending/highest first)
            2. timestamp (ascending/earliest first for ties)

            Returns empty list if ledger contains no entries.

        Note:
            Useful for market analysis, top-k selection, and performance
            visualization. Maintains same deterministic ordering as
            get_best_policy().
        """
        entries = self.ledger.read_all()
        
        if not entries:
            return []
        
        # Sort by reward (descending), then timestamp (ascending)
        sorted_entries = sorted(
            entries,
            key=lambda e: (-e.verified_reward, e.timestamp)
        )
        
        return [
            BestPolicyReference(
                policy_hash=e.policy_hash,
                verified_reward=e.verified_reward,
                agent_id=e.agent_id
            )
            for e in sorted_entries
        ]


# Convenience function for simple use cases
def select_best_policy(ledger: PolicyLedger) -> Optional[BestPolicyReference]:
    """
    Convenience function: Select best policy from ledger.
    
    Args:
        ledger: Source of verified entries
        
    Returns:
        BestPolicyReference if available, None if empty ledger
        
    Usage:
        >>> best = select_best_policy(ledger)
        >>> if best:
        ...     print(f"Best policy: {best.policy_hash} ({best.verified_reward})")
    """
    marketplace = PolicyMarketplace(ledger)
    return marketplace.get_best_policy()
