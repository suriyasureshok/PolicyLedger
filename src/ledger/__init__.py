"""
ledger

Purpose:
- What this package represents: Tamper-evident storage module for verified policy claims using hash chaining

Public Exports:
- LedgerEntry
- PolicyLedger
- verify_chain_integrity

Usage:
    from src.ledger import LedgerEntry, PolicyLedger
"""

from src.ledger.ledger import (
    LedgerEntry,
    PolicyLedger,
    verify_chain_integrity
)

__all__ = [
    "LedgerEntry",
    "PolicyLedger",
    "verify_chain_integrity"
]
