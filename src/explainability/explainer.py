"""
Main Explainer — Phase 11 Implementation

Chooses between Fallback and Gemini explainers.
Same interface, different implementations.
"""

from typing import Optional
from .base import BaseExplainer
from .fallback import FallbackExplainer
from .gemini import GeminiExplainer
from .metrics import ExplanationMetrics


class Explainer:
    """
    Main explainer that delegates to implementations.

    Defaults to Gemini if available, falls back to template.
    """

    def __init__(self, use_gemini: bool = True, api_key: Optional[str] = None):
        self.fallback = FallbackExplainer()
        self.gemini = GeminiExplainer(api_key, self.fallback) if use_gemini else None

    def explain(self, metrics: ExplanationMetrics) -> str:
        """
        Generate explanation.

        Tries Gemini first, falls back to template.
        """
        if self.gemini:
            explanation = self.gemini.explain(metrics)
            if explanation:  # If Gemini worked
                return explanation

        # Fallback
        return self.fallback.explain(metrics)