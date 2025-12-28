"""
Verification Layer

Trust is derived from replayability, not reputation.
"""

from src.verifier.verifier import (
    VerificationResult,
    VerificationStatus,
    PolicyVerifier,
    verify_claim
)

__all__ = [
    "VerificationResult",
    "VerificationStatus",
    "PolicyVerifier",
    "verify_claim"
]
