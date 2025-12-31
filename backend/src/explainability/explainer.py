"""
Main Explainer — Phase 11 Implementation

Uses template-based fallback explainer for policy explanations.
Same interface, simple implementation.
"""

from typing import Optional
from .base import BaseExplainer
from .fallback import FallbackExplainer
from .metrics import ExplanationMetrics


class Explainer:
    """
    Main explainer using template-based implementation.
    """

    def __init__(self, use_gemini: bool = False, api_key: Optional[str] = None):
        self.fallback = FallbackExplainer()

    def explain(self, metrics: ExplanationMetrics) -> str:
        """
        Generate explanation using template-based fallback.
        """
        return self.fallback.explain(metrics)