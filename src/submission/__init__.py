"""
submission

Purpose:
- What this package represents: Quarantine zone for collecting policy claims before verification

Public Exports:
- SubmissionCollector
- Submission

Usage:
    from src.submission import SubmissionCollector, Submission
"""

from src.submission.collector import SubmissionCollector, Submission

__all__ = [
    "SubmissionCollector",
    "Submission",
]
