"""
Gemini Explainer — AI-Powered Explanation

Uses Google Gemini to generate natural language explanations.
Narrates behavior, does not invent intelligence.
"""

import os
from typing import Optional
from .base import BaseExplainer
from .metrics import ExplanationMetrics

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GeminiExplainer(BaseExplainer):
    """
    Gemini-based explanation generator.

    Summarizes behavior in natural language.
    Falls back to template if Gemini unavailable.
    """

    def __init__(self, api_key: Optional[str] = None, fallback_explainer: Optional[BaseExplainer] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
        self.fallback = fallback_explainer

    def explain(self, metrics: ExplanationMetrics) -> str:
        if not self.model:
            # Fallback to simple template
            return self._fallback_explain(metrics)

        # Construct prompt
        prompt = self._build_prompt(metrics)

        try:
            response = self.model.generate_content(prompt)
            explanation = response.text.strip()
            # Ensure it's one paragraph
            explanation = explanation.replace('\n', ' ').strip()
            return explanation
        except Exception as e:
            # Fallback on error
            return self._fallback_explain(metrics)

    def _build_prompt(self, metrics: ExplanationMetrics) -> str:
        """Build structured prompt for Gemini."""
        env = metrics.environment_name
        reward = metrics.verified_reward
        baseline = metrics.baseline_reward
        stats = metrics.behavior_stats

        prompt = f"You are explaining the behavior of a reinforcement learning policy to a non-technical judge. Do not mention algorithms, equations, or internal model details.\n\n"
        prompt += f"In an {env} environment, a policy achieved a verified reward of {reward:.2f}"
        if baseline is not None:
            prompt += f", compared to a baseline reward of {baseline:.2f}"
        prompt += ". "

        # Add behavior stats
        stat_desc = []
        if "save_percentage" in stats:
            stat_desc.append(f"used the SAVE action in {stats['save_percentage']*100:.0f}% of time slots")
        if "use_percentage" in stats:
            stat_desc.append(f"used the USE action in {stats['use_percentage']*100:.0f}% of time slots")
        if "avg_battery" in stats:
            stat_desc.append(f"maintained an average battery level of {stats['avg_battery']*100:.0f}%")
        if "survived" in stats:
            stat_desc.append("survived the full time horizon" if stats["survived"] else "did not survive the full time horizon")

        if stat_desc:
            prompt += "The policy " + ", ".join(stat_desc) + ". "

        prompt += "Explain why this policy performed as it did in simple terms."

        return prompt

    def _fallback_explain(self, metrics: ExplanationMetrics) -> str:
        """Simple fallback explanation."""
        if self.fallback:
            return self.fallback.explain(metrics)
        else:
            env = metrics.environment_name
            reward = metrics.verified_reward
            baseline = metrics.baseline_reward

            if baseline is None:
                return f"The policy achieved a reward of {reward:.2f} in the {env} environment through effective resource management."
            else:
                diff = reward - baseline
                if diff > 0:
                    return f"The policy outperformed the baseline by {diff:.2f} in the {env} environment, demonstrating better decision-making."
                else:
                    return f"The policy underperformed the baseline by {abs(diff):.2f} in the {env} environment."