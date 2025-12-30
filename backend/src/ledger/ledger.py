"""
ledger.py

Tamper-evident policy storage using hash chaining.

Detailed description:
- What problem this module solves: Provides immutable, tamper-evident storage for verified policy claims using blockchain-inspired hash chaining
- What it does NOT do: Does not perform policy verification, training, or modification; focuses solely on secure storage and integrity checking
- Any assumptions or constraints: Assumes policies are pre-verified; relies on SHA-256 for cryptographic integrity; requires append-only operations

Main Components:
- LedgerEntry: Immutable data structure for policy verification records
- PolicyLedger: Main class with append-only operations and integrity verification
- verify_chain_integrity(): Function for tamper detection through hash chain validation
- compute_entry_hash(): Function for SHA-256 hash computation of entries

Dependencies:
- hashlib: For cryptographic hash functions
- json: For entry serialization and deserialization
- datetime: For timestamp generation
- pathlib: For file system operations
- typing: For type hints and annotations

Author: PolicyLedger Team
Created: 2025-12-28

TODO: Google Cloud Integration
- Firestore: Store ledger entries in append-only Firestore collection
- Cloud Functions: Trigger on new entries to update marketplace ranking
- Security Rules: Enforce append-only via Firestore security rules
- Cloud Logging: Audit all ledger operations with structured logs
"""

from typing import List, NamedTuple, Optional
from datetime import datetime
import hashlib
import json
from pathlib import Path


class LedgerEntry(NamedTuple):
    """
    Immutable ledger entry for a verified policy claim.

    Represents a single verified policy record in the tamper-evident ledger.
    Each entry contains the essential information about a policy that has
    passed verification, with cryptographic links to maintain chain integrity.

    Attributes:
        policy_hash: SHA-256 hash of the policy artifact
        verified_reward: Reward confirmed by the verification layer
        agent_id: Unique identifier of the agent that created the policy
        timestamp: ISO 8601 formatted timestamp of verification
        previous_hash: SHA-256 hash of the previous ledger entry (or "genesis")
        current_hash: SHA-256 hash of this entry for chain verification

    Note:
        This structure contains ONLY verified information - no training metadata,
        claimed rewards, or policy artifacts. It serves as an immutable record
        of what was verified and when.
    """
    policy_hash: str
    verified_reward: float
    agent_id: str
    timestamp: str
    previous_hash: str
    current_hash: str
    
    def __repr__(self) -> str:
        return (
            f"LedgerEntry(\n"
            f"  policy_hash='{self.policy_hash[:16]}...',\n"
            f"  verified_reward={self.verified_reward:.3f},\n"
            f"  agent_id='{self.agent_id}',\n"
            f"  timestamp='{self.timestamp}',\n"
            f"  previous_hash='{self.previous_hash[:16]}...',\n"
            f"  current_hash='{self.current_hash[:16]}...'\n"
            f")"
        )


# =============================================================================
# HASH CHAIN LOGIC
# =============================================================================

def compute_entry_hash(
    policy_hash: str,
    verified_reward: float,
    agent_id: str,
    timestamp: str,
    previous_hash: str
) -> str:
    """
    Compute deterministic hash for ledger entry.

    Creates the cryptographic link in the hash chain. Any modification to
    an existing entry will break all subsequent hashes, making tampering
    immediately detectable.

    Args:
        policy_hash: SHA-256 hash of the policy artifact
        verified_reward: Reward value confirmed by verification layer
        agent_id: Unique identifier of the agent
        timestamp: ISO 8601 formatted timestamp
        previous_hash: SHA-256 hash of the previous ledger entry

    Returns:
        SHA-256 hash as 64-character hexadecimal string

    Note:
        Hash is computed deterministically from all entry fields.
        Same inputs always produce the same hash.
    """
    # Create deterministic string representation
    # Format: "field1|field2|field3|..." for clarity
    hash_input = f"{policy_hash}|{verified_reward:.6f}|{agent_id}|{timestamp}|{previous_hash}"
    
    # Compute SHA-256 hash
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def verify_chain_integrity(entries: List[LedgerEntry]) -> tuple[bool, Optional[str]]:
    """
    Verify that a list of ledger entries forms a valid hash chain.

    Performs comprehensive validation of the cryptographic hash chain to detect
    any tampering, modification, or corruption of the ledger entries.

    Validation checks:
        1. First entry has previous_hash = "genesis"
        2. Each entry current_hash matches computed hash of its data
        3. Each entry previous_hash matches the previous entry current_hash
        4. Chain continuity is maintained throughout

    Args:
        entries: List of LedgerEntry objects in chronological order

    Returns:
        Tuple of (is_valid, error_message) where:
        - is_valid: True if all checks pass, False if any validation fails
        - error_message: Detailed description of the validation failure,
          or None if validation succeeds

    Note:
        Can detect: modified entries, deleted entries, reordered entries,
        and any other form of tampering that breaks the hash chain.
    """
    if len(entries) == 0:
        return True, None  # Empty ledger is valid
    
    # Check first entry
    first = entries[0]
    if first.previous_hash != "genesis":
        return False, f"First entry must have previous_hash='genesis', got '{first.previous_hash}'"
    
    # Verify first entry's hash
    expected_hash = compute_entry_hash(
        first.policy_hash,
        first.verified_reward,
        first.agent_id,
        first.timestamp,
        first.previous_hash
    )
    if first.current_hash != expected_hash:
        return False, f"Entry 0 hash mismatch: expected {expected_hash[:16]}..., got {first.current_hash[:16]}..."
    
    # Check chain continuity
    for i in range(1, len(entries)):
        entry = entries[i]
        prev_entry = entries[i - 1]
        
        # Check previous_hash points to previous entry
        if entry.previous_hash != prev_entry.current_hash:
            return False, (
                f"Chain break at entry {i}: "
                f"previous_hash={entry.previous_hash[:16]}... "
                f"but prev current_hash={prev_entry.current_hash[:16]}..."
            )
        
        # Verify current entry's hash
        expected_hash = compute_entry_hash(
            entry.policy_hash,
            entry.verified_reward,
            entry.agent_id,
            entry.timestamp,
            entry.previous_hash
        )
        if entry.current_hash != expected_hash:
            return False, (
                f"Entry {i} hash mismatch: "
                f"expected {expected_hash[:16]}..., "
                f"got {entry.current_hash[:16]}..."
            )
    
    return True, None


# =============================================================================
# LEDGER INTERFACE
# =============================================================================

class PolicyLedger:
    """
    Tamper-evident, append-only policy ledger.

    Implements blockchain-inspired hash chaining to provide immutable storage
    for verified policy claims. Any attempt to modify or delete past entries
    is immediately detectable through chain verification.

    Core Properties:
        - Append-only: New entries can be added but existing ones are immutable
        - Tamper-evident: Cryptographic hash chaining detects any modifications
        - Trust-preserving: Maintains integrity of verification records
        - Storage-agnostic: Interface allows different storage implementations

    Responsibilities:
        - Store verified policy claims with cryptographic integrity
        - Provide read access to ledger entries
        - Enable tamper detection through chain verification

    Non-Responsibilities:
        - Policy verification (handled by verifier layer)
        - Policy ranking (handled by marketplace layer)
        - Policy storage (artifacts stored separately)
        - Training or execution (handled by agent/consumer layers)

    Attributes:
        storage_path: Path to JSON file for persistent storage
        _entries: In-memory list of ledger entries
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize ledger with optional storage path.

        Args:
            storage_path: Path to JSON file for persistent storage.
                If None, defaults to "ledger.json" in current directory.
        """
        self.storage_path = Path(storage_path or "ledger.json")
        self._entries: List[LedgerEntry] = []
        self._load_from_storage()
    
    # =========================================================================
    # RESPONSIBILITY 1: APPEND VERIFIED ENTRY
    # =========================================================================
    
    def append(
        self,
        policy_hash: str,
        verified_reward: float,
        agent_id: str
    ) -> LedgerEntry:
        """
        Append a verified policy claim to the ledger.

        Called ONLY after the verification layer has confirmed the policy
        validity and reward. Creates a new immutable entry with cryptographic
        hash chaining to maintain tamper-evident properties.

        Process:
            1. Determine previous hash (genesis for first entry)
            2. Generate current timestamp
            3. Compute cryptographic hash of entry data
            4. Create and store LedgerEntry
            5. Persist to storage

        Args:
            policy_hash: SHA-256 hash of the verified policy artifact
            verified_reward: Reward value confirmed by verification layer
            agent_id: Unique identifier of the agent that created the policy

        Returns:
            The newly created LedgerEntry with all computed fields

        Note:
            This method trusts the caller (verification layer) completely.
            It performs no validation of the provided data.
        """
        # Get previous entry hash
        if len(self._entries) == 0:
            previous_hash = "genesis"
        else:
            previous_hash = self._entries[-1].current_hash
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Compute current hash
        current_hash = compute_entry_hash(
            policy_hash,
            verified_reward,
            agent_id,
            timestamp,
            previous_hash
        )
        
        # Create entry
        entry = LedgerEntry(
            policy_hash=policy_hash,
            verified_reward=verified_reward,
            agent_id=agent_id,
            timestamp=timestamp,
            previous_hash=previous_hash,
            current_hash=current_hash
        )
        
        # Append to memory
        self._entries.append(entry)
        
        # Persist to storage
        self._save_to_storage()
        
        return entry
    
    # =========================================================================
    # RESPONSIBILITY 2: READ LEDGER
    # =========================================================================
    
    def read_all(self) -> List[LedgerEntry]:
        """
        Return all ledger entries in chronological order.

        Provides read access to the complete ledger history. Entries are
        returned in the order they were appended, maintaining the immutable
        sequence of verified policy claims.

        Returns:
            List of LedgerEntry objects in append order (oldest first)

        Note:
            Returns a copy to prevent external modification of ledger state.
            The ledger itself remains immutable.
        """
        return self._entries.copy()
    
    def get_latest(self) -> Optional[LedgerEntry]:
        """
        Get the most recent ledger entry.
        
        Returns:
            Latest LedgerEntry or None if ledger is empty
        """
        if len(self._entries) == 0:
            return None
        return self._entries[-1]
    
    def count(self) -> int:
        """Get total number of entries."""
        return len(self._entries)
    
    # =========================================================================
    # CHAIN VERIFICATION
    # =========================================================================
    
    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify that the ledger hash chain is intact and untampered.

        Checks the cryptographic integrity of the entire ledger by validating
        the hash chain. Any modification to past entries will break the chain
        and be detected immediately.

        Returns:
            Tuple of (is_valid, error_message) where:
            - is_valid: True if chain is intact, False if tampered
            - error_message: Description of the problem if validation fails,
              None if validation succeeds

        Note:
            This method should be called regularly by audit tools or before
            critical operations like policy ranking.
        """
        return verify_chain_integrity(self._entries)
    
    # =========================================================================
    # STORAGE (FALLBACK IMPLEMENTATION)
    # =========================================================================
    
    def _load_from_storage(self):
        """
        Load ledger from JSON file.
        
        This is the fallback implementation.
        
        Rules:
            - If file does not exist -> start with empty ledger
            - If file corrupted -> FAIL LOUDLY (do not auto-repair)
        """
        if not self.storage_path.exists():
            self._entries = []
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Reconstruct entries
            entries = []
            for entry_data in data.get("entries", []):
                entry = LedgerEntry(
                    policy_hash=entry_data["policy_hash"],
                    verified_reward=entry_data["verified_reward"],
                    agent_id=entry_data["agent_id"],
                    timestamp=entry_data["timestamp"],
                    previous_hash=entry_data["previous_hash"],
                    current_hash=entry_data["current_hash"]
                )
                entries.append(entry)
            
            self._entries = entries
            
            # Verify integrity on load
            is_valid, error = self.verify_integrity()
            if not is_valid:
                raise RuntimeError(
                    f"LEDGER CORRUPTION DETECTED: {error}\n"
                    f"Trust preserved by halting. Never auto-repair ledger."
                )
        
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"LEDGER CORRUPTION: JSON malformed: {e}\n"
                f"Trust preserved by halting. Never auto-repair ledger."
            )
        except Exception as e:
            raise RuntimeError(
                f"LEDGER CORRUPTION: {e}\n"
                f"Trust preserved by halting. Never auto-repair ledger."
            )
    
    def _save_to_storage(self):
        """
        Save ledger to JSON file.
        
        This is the fallback implementation.
        """
        # Convert entries to serializable format
        entries_data = []
        for entry in self._entries:
            entries_data.append({
                "policy_hash": entry.policy_hash,
                "verified_reward": entry.verified_reward,
                "agent_id": entry.agent_id,
                "timestamp": entry.timestamp,
                "previous_hash": entry.previous_hash,
                "current_hash": entry.current_hash
            })
        
        # Write to file with atomic write
        data = {
            "ledger_version": "1.0",
            "total_entries": len(entries_data),
            "entries": entries_data
        }
        
        # Write to temp file first, then atomic rename
        temp_path = self.storage_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Atomic rename (safer than direct write)
        temp_path.replace(self.storage_path)
    
    def __repr__(self) -> str:
        return (
            f"PolicyLedger(\n"
            f"  total_entries={len(self._entries)},\n"
            f"  storage='{self.storage_path}',\n"
            f"  integrity={'VALID' if self.verify_integrity()[0] else 'INVALID'}\n"
            f")"
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_ledger(storage_path: Optional[str] = None) -> PolicyLedger:
    """
    Create or load a policy ledger.

    Args:
        storage_path: Path for ledger storage

    Returns:
        PolicyLedger instance
    """
    return PolicyLedger(storage_path)
