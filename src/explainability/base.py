"""
Base Explainer Interface

Two implementations: Fallback and Gemini.
"""

from abc import ABC, abstractmethod
from .metrics import ExplanationMetrics


class BaseExplainer(ABC):
    """
    Abstract base class for explainers.
    """

    @abstractmethod
    def explain(self, metrics: ExplanationMetrics) -> str:
        """
        Generate a human-readable explanation paragraph.

        Args:
            metrics: High-level outcomes only

        Returns:
            One paragraph explanation
        """
        pass