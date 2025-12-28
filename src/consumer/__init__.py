"""
consumer

Policy Reuse module for instant intelligence sharing.

Detailed description:
- Enables instant policy reuse without retraining
- Compares reused policies against baseline strategies
- Provides the "wow moment" of verified intelligence sharing

Main Components:
- PolicyConsumer: Main class for policy loading and execution
- BaselinePolicy: Enum for baseline comparison strategies
- reuse_best_policy(): Convenience function for marketplace integration

Dependencies:
- src.shared.env: EnergySlotEnv for policy execution
- src.agent.state: State discretization
- src.agent.policy: Policy serialization/deserialization

Author: PolicyLedger Team
Created: 2025-12-28
"""

from .reuse import PolicyConsumer, BaselinePolicy, reuse_best_policy

__all__ = ["PolicyConsumer", "BaselinePolicy", "reuse_best_policy"]
