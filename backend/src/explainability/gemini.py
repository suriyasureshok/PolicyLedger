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

        prompt = f"You are explaining the behavior of a cybersecurity reinforcement learning policy to a technical audience. Focus on defensive strategy and threat response patterns.\n\n"
        prompt += f"In a {env}, a policy achieved a verified reward of {reward:.2f}"
        if baseline is not None:
            diff = reward - baseline
            if diff > 0:
                prompt += f", which is {diff:.2f} points better than the average policy"
            else:
                prompt += f", which is {abs(diff):.2f} points below the average policy"
        prompt += ". "

        # Add behavior stats for cyber defense
        stat_desc = []
        if "ignore_percentage" in stats:
            stat_desc.append(f"ignored {stats['ignore_percentage']*100:.0f}% of threats")
        if "monitor_percentage" in stats:
            stat_desc.append(f"monitored {stats['monitor_percentage']*100:.0f}% of situations")
        if "rate_limit_percentage" in stats:
            stat_desc.append(f"applied rate limiting {stats['rate_limit_percentage']*100:.0f}% of the time")
        if "block_ip_percentage" in stats:
            stat_desc.append(f"blocked IPs {stats['block_ip_percentage']*100:.0f}% of the time")
        if "isolate_percentage" in stats:
            stat_desc.append(f"isolated services {stats['isolate_percentage']*100:.0f}% of the time")
        if "total_states_covered" in stats:
            coverage = (stats["total_states_covered"] / 108) * 100 if stats["total_states_covered"] else 0
            stat_desc.append(f"learned {stats['total_states_covered']} out of 108 possible attack scenarios ({coverage:.0f}% coverage)")

        if stat_desc:
            prompt += "The policy " + ", ".join(stat_desc) + ". "

        prompt += "Explain in 2-3 sentences why this defensive strategy performed as it did, focusing on threat response patterns and security trade-offs. Be specific about what makes this policy effective or ineffective at protecting the system."

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