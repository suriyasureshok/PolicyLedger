"""
Environment for deterministic energy scheduling problem.
The agent must decide to USE or SAVE energy at each time slot to maximize total reward
without exhausting the battery early.

NOTE: This environment is kept for backwards compatibility.
New development should use src.environments.cyber_env.CyberDefenseEnv.
"""

from typing import Tuple, Dict
import numpy as np
from src.environments.base_env import BaseEnv


class EnergySlotEnv(BaseEnv):
    """
    Deterministic energy scheduling environment.

    The agent decides whether to USE or SAVE energy at each time slot
    to maximize total reward without exhausting the battery early.
    """
    SAVE = 0
    USE = 1

    def __init__(
        self,
        time_slots: int = 24,
        battery_capacity: float = 1.0,
        energy_cost: float = 0.1,
        seed: int = 42,
    ):
        self.time_slots = time_slots
        self.battery_capacity = battery_capacity
        self.energy_cost = energy_cost
        self.seed = seed

        self._rng = np.random.RandomState(seed)
        self.demand_schedule = self._generate_demand()

        self.reset()

    # -----------------------------
    # Internal helpers
    # -----------------------------

    def _generate_demand(self) -> np.ndarray:
        """
        Generate a deterministic binary demand schedule.
        1 → energy needed
        0 → no energy needed
        """
        # Fixed randomness via seed
        return self._rng.choice([0, 1], size=self.time_slots, p=[0.5, 0.5])

    # -----------------------------
    # Public API
    # -----------------------------

    def reset(self) -> Dict:
        """
        Reset environment to initial state.
        """
        self.current_step = 0
        self.battery_level = self.battery_capacity
        self.done = False

        return self._get_state()

    def step(self, action: int) -> Tuple[Dict, float, bool]:
        """
        Take an action and advance the environment by one time step.
        """
        if self.done:
            raise RuntimeError("Episode has already terminated. Call reset().")

        reward = 0.0
        demand = self.demand_schedule[self.current_step]

        # Apply action
        if action == self.USE:
            self.battery_level -= self.energy_cost

            if demand == 1:
                reward += 1.0
            else:
                reward -= 1.0

        elif action == self.SAVE:
            # No battery change, no immediate reward
            reward += 0.0

        else:
            raise ValueError(f"Invalid action: {action}")

        # Check battery exhaustion
        if self.battery_level <= 0:
            reward -= 2.0
            self.done = True
            return self._get_state(), reward, self.done

        # Advance time
        self.current_step += 1

        # Check terminal condition (end of horizon)
        if self.current_step >= self.time_slots:
            reward += 5.0
            self.done = True

        return self._get_state(), reward, self.done

    def _get_state(self) -> Dict:
        """
        Return the current observable state.
        """
        demand = (
            self.demand_schedule[self.current_step]
            if self.current_step < self.time_slots
            else 0
        )

        return {
            "time_slot": self.current_step,
            "battery_level": round(self.battery_level, 3),
            "demand": int(demand),
        }
