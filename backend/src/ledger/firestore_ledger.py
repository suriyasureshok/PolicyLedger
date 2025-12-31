"""
Firestore Ledger Implementation
Cloud-based tamper-evident ledger using Google Cloud Firestore
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional
from ..shared.gcp_config import get_firestore_client, gcp_config


class FirestoreLedger:
    """
    Firestore-backed tamper-evident ledger
    
    Features:
    - Distributed storage with automatic replication
    - Real-time updates across clients
    - Append-only enforced via Firestore rules
    - Global accessibility
    """
    
    def __init__(self, collection_name: str = "ledger_entries"):
        self.collection_name = collection_name
        self.client = get_firestore_client()
        
        if self.client is None:
            raise RuntimeError("Firestore client not available. Enable GCP integration.")
    
    def add_entry(
        self,
        policy_hash: str,
        agent_id: str,
        verified_reward: float,
        previous_hash: str = "0" * 64
    ) -> Dict:
        """Add a new entry to the ledger"""
        
        # Get the latest entry to chain from
        latest = self.get_latest_entry()
        if latest:
            previous_hash = latest.get("current_hash", "0" * 64)
        
        # Create entry
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Compute current hash
        hash_input = f"{policy_hash}{verified_reward}{timestamp}{previous_hash}"
        current_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        entry = {
            "policy_hash": policy_hash,
            "agent_id": agent_id,
            "verified_reward": verified_reward,
            "timestamp": timestamp,
            "previous_hash": previous_hash,
            "current_hash": current_hash
        }
        
        # Add to Firestore (use current_hash as document ID for idempotency)
        doc_ref = self.client.collection(self.collection_name).document(current_hash)
        doc_ref.set(entry)
        
        return entry
    
    def get_all_entries(self) -> List[Dict]:
        """Retrieve all ledger entries ordered by timestamp"""
        docs = self.client.collection(self.collection_name)\
            .order_by("timestamp")\
            .stream()
        
        return [doc.to_dict() for doc in docs]
    
    def get_latest_entry(self) -> Optional[Dict]:
        """Get the most recent ledger entry"""
        docs = self.client.collection(self.collection_name)\
            .order_by("timestamp", direction="DESCENDING")\
            .limit(1)\
            .stream()
        
        entries = [doc.to_dict() for doc in docs]
        return entries[0] if entries else None
    
    def get_entry_by_policy_hash(self, policy_hash: str) -> Optional[Dict]:
        """Find entry by policy hash"""
        docs = self.client.collection(self.collection_name)\
            .where("policy_hash", "==", policy_hash)\
            .limit(1)\
            .stream()
        
        entries = [doc.to_dict() for doc in docs]
        return entries[0] if entries else None
    
    def verify_chain_integrity(self) -> Dict:
        """Verify the integrity of the hash chain"""
        entries = self.get_all_entries()
        
        if not entries:
            return {
                "is_valid": True,
                "total_entries": 0,
                "verified_at": datetime.utcnow().isoformat() + "Z"
            }
        
        # Check first entry
        if entries[0]["previous_hash"] != "0" * 64:
            return {
                "is_valid": False,
                "error": "First entry does not point to genesis",
                "total_entries": len(entries),
                "verified_at": datetime.utcnow().isoformat() + "Z"
            }
        
        # Verify each subsequent entry
        for i in range(len(entries)):
            entry = entries[i]
            
            # Recompute hash
            hash_input = f"{entry['policy_hash']}{entry['verified_reward']}{entry['timestamp']}{entry['previous_hash']}"
            expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            if entry["current_hash"] != expected_hash:
                return {
                    "is_valid": False,
                    "error": f"Hash mismatch at entry {i}",
                    "total_entries": len(entries),
                    "verified_at": datetime.utcnow().isoformat() + "Z"
                }
            
            # Check chain linkage
            if i > 0 and entry["previous_hash"] != entries[i-1]["current_hash"]:
                return {
                    "is_valid": False,
                    "error": f"Chain break at entry {i}",
                    "total_entries": len(entries),
                    "verified_at": datetime.utcnow().isoformat() + "Z"
                }
        
        return {
            "is_valid": True,
            "total_entries": len(entries),
            "verified_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def get_stats(self) -> Dict:
        """Get ledger statistics"""
        entries = self.get_all_entries()
        
        if not entries:
            return {
                "total_entries": 0,
                "total_agents": 0,
                "average_reward": 0.0
            }
        
        unique_agents = set(entry["agent_id"] for entry in entries)
        total_reward = sum(entry["verified_reward"] for entry in entries)
        
        return {
            "total_entries": len(entries),
            "total_agents": len(unique_agents),
            "average_reward": total_reward / len(entries),
            "latest_entry": entries[-1]
        }
