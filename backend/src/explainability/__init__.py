"""
Explainability Module — Phase 11

Converts verified outcomes into human language.

PURPOSE:
    Answer ONE question: "Why did this policy win, in terms a human can understand?"

NOT:
    - How RL works
    - Internal algorithms
    - Training details

ONLY:
    - Compare policy vs baseline
    - Mention key behavioral differences
    - Mention outcome differences
"""

from .explainer import Explainer
from .metrics import ExplanationMetrics

__all__ = ["Explainer", "ExplanationMetrics"]