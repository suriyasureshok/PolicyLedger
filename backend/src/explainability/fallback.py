"""
Fallback Explainer — Template-Based

Mandatory implementation.
No ML jargon, no algorithms.
"""

from .base import BaseExplainer
from .metrics import ExplanationMetrics


class FallbackExplainer(BaseExplainer):
    """
    Template-based explanation generator.

    Compares policy vs baseline, mentions key differences.
    """

    def explain(self, metrics: ExplanationMetrics) -> str:
        env = metrics.environment_name
        policy = metrics.policy_identifier
        reward = metrics.verified_reward
        baseline = metrics.baseline_reward
        stats = metrics.behavior_stats

        # Basic template
        if baseline is None:
            # No baseline case
            explanation = f"In the {env} environment, the policy {policy} achieved a verified reward of {reward:.2f}. "
            explanation += self._describe_behavior(stats)
            explanation += " This performance demonstrates effective decision-making aligned with the environment's goals."
        else:
            improvement = reward - baseline
            if improvement > 0:
                explanation = f"In the {env} environment, the policy {policy} outperformed the baseline by achieving a verified reward of {reward:.2f} compared to {baseline:.2f}. "
                explanation += self._describe_behavior_comparison(stats)
                explanation += f" As a result, it accumulated {improvement:.2f} more reward, showing superior strategy in managing resources."
            elif improvement == 0:
                explanation = f"In the {env} environment, the policy {policy} matched the baseline performance with a verified reward of {reward:.2f}. "
                explanation += self._describe_behavior(stats)
                explanation += " While no improvement was gained, it maintained competitive results."
            else:
                explanation = f"In the {env} environment, the policy {policy} underperformed the baseline, achieving {reward:.2f} compared to {baseline:.2f}. "
                explanation += self._describe_behavior(stats)
                explanation += " This suggests room for improvement in strategy."

        return explanation

    def _describe_behavior(self, stats: dict) -> str:
        """Describe behavior from stats."""
        desc = ""
        if "save_percentage" in stats:
            desc += f"It used the SAVE action {stats['save_percentage']*100:.0f}% of the time. "
        if "use_percentage" in stats:
            desc += f"It used the USE action {stats['use_percentage']*100:.0f}% of the time. "
        if "avg_battery" in stats:
            desc += f"The average battery level was {stats['avg_battery']*100:.0f}%. "
        if "survived" in stats:
            desc += "It survived the full time horizon. " if stats["survived"] else "It did not survive the full time horizon. "
        return desc

    def _describe_behavior_comparison(self, stats: dict) -> str:
        """Describe how behavior led to better outcomes."""
        # For now, simple description; can be enhanced
        desc = self._describe_behavior(stats)
        # Add comparison if possible, but since no baseline stats, keep simple
        return desc