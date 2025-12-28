"""
Policy Ledger — Tamper-Evident Memory

PURPOSE:
    Answer ONE question: "Once a policy is verified as valid, 
    how do we record it so it cannot be silently altered or erased?"

PROPERTIES:
    - Append-only
    - Passive
    - Trust-preserving

NOT A:
    - Verifier
    - Ranker
    - Database with updates
    - Crypto system

MENTAL MODEL:
    Ledger = official mark register in a school
    Marks written once, no erasing, no rewriting.
    If someone tampers → detectable.
"""

from typing import List, NamedTuple, Optional
from datetime import datetime
import hashlib
import json
from pathlib import Path


class LedgerEntry(NamedTuple):
    """
    Immutable ledger entry for a verified policy.
    
    This is the FINAL & FROZEN schema.
    
    Fields:
        policy_hash: SHA-256 hash of policy artifact
        verified_reward: Reward confirmed by verifier
        agent_id: Agent identifier
        timestamp: ISO format timestamp
        previous_hash: Hash of previous ledger entry (or "genesis")
        current_hash: Hash of this entry (for chain verification)
    
    What it does NOT contain:
        ❌ Training metadata
        ❌ Claimed reward
        ❌ Policy artifact
        ❌ Ranking info
    
    Ledger stores truth only, not claims.
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
    
    This creates the hash chain:
        current_hash = hash(policy_hash + verified_reward + 
                          agent_id + timestamp + previous_hash)
    
    If any old entry changes → all future hashes break.
    That's tamper-evident, not crypto hype.
    
    Args:
        policy_hash: Policy artifact hash
        verified_reward: Verified reward value
        agent_id: Agent identifier
        timestamp: ISO timestamp
        previous_hash: Hash of previous entry
    
    Returns:
        SHA-256 hash as hexadecimal string
    
    Rules:
        - Deterministic: same inputs → same hash
        - No randomness
        - No salt
        - No timestamps in hash computation itself
    """
    # Create deterministic string representation
    # Format: "field1|field2|field3|..." for clarity
    hash_input = f"{policy_hash}|{verified_reward:.6f}|{agent_id}|{timestamp}|{previous_hash}"
    
    # Compute SHA-256 hash
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def verify_chain_integrity(entries: List[LedgerEntry]) -> tuple[bool, Optional[str]]:
    """
    Verify that ledger chain is intact and untampered.
    
    This checks:
    1. First entry has previous_hash = "genesis"
    2. Each entry's current_hash is correctly computed
    3. Each entry's previous_hash matches previous entry's current_hash
    
    Args:
        entries: List of ledger entries in order
    
    Returns:
        (is_valid, error_message)
        - (True, None) if chain is intact
        - (False, reason) if tampering detected
    
    This is how we detect:
        - Modified entries
        - Deleted entries
        - Reordered entries
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
    
    This is storage-agnostic interface.
    Implementations provide actual storage (JSON, Firestore, etc.)
    
    Responsibilities:
    1. Append verified entries
    2. Read ledger entries
    
    Does NOT:
        ❌ Verify rewards
        ❌ Check policy validity
        ❌ Reject duplicates
        ❌ Sort entries
        ❌ Modify past entries
        ❌ Rank policies
        ❌ Decide best policy
        ❌ Accept unverified data
    
    Ledger is dumb memory. That's its strength.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize ledger.
        
        Args:
            storage_path: Path for JSON storage (fallback implementation)
                         If None, uses default: "ledger.json"
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
        Append a verified policy to the ledger.
        
        This is called ONLY after verifier says VALID.
        If verifier says INVALID → ledger never sees it.
        
        Process:
        1. Read last ledger entry (if exists)
        2. Compute previous_hash
        3. Generate timestamp
        4. Compute current_hash
        5. Append entry
        6. Persist to storage
        
        Args:
            policy_hash: Verified policy artifact hash
            verified_reward: Reward confirmed by verifier
            agent_id: Agent identifier
        
        Returns:
            The created LedgerEntry
        
        Rules:
            - Does NOT verify the reward
            - Does NOT check policy validity
            - Does NOT reject duplicates
            - Just appends the fact
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
        Return all ledger entries in order.
        
        Returns:
            List of LedgerEntry in append order
        
        Rules:
            - Does NOT filter
            - Does NOT rank
            - Does NOT modify
            - Does NOT fix inconsistencies
            - Returns raw truth
        
        Ledger is memory, not intelligence.
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
        Verify that ledger chain is intact and untampered.
        
        Returns:
            (is_valid, error_message)
        
        This should be called by marketplace or audit tools.
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
            - If file doesn't exist → start with empty ledger
            - If file corrupted → FAIL LOUDLY (don't auto-repair)
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
            f"  integrity={'✅ INTACT' if self.verify_integrity()[0] else '❌ COMPROMISED'}\n"
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
