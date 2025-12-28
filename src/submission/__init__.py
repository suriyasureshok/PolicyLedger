"""
Submission Layer Module

This is the exam submission desk, NOT the examiner.

Purpose: Accept claims without judgment
- Does NOT verify rewards
- Does NOT compare agents
- Does NOT reject claims
- Does NOT modify artifacts
- Does NOT decide trust

If it does anything intelligent, the design is broken.
"""

from src.submission.collector import SubmissionCollector, Submission

__all__ = [
    "SubmissionCollector",
    "Submission",
]
