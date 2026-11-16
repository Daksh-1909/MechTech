"""Normal healthy operation scenario.

A well-maintained motor running at steady load with minimal noise.
Temperature stays near thermal equilibrium; vibration is at the
healthy baseline.

Expected ranges (simulated only — not real sensor values):
  temperature_c  : 50–65 °C
  vibration_value: 0.03–0.09 (simulated_index)
"""

import random
from typing import Any


SCENARIO_ID = "normal"
SCENARIO_LABEL = "normal"


def perturbation(step: int, rng: random.Random) -> dict[str, Any]:  # noqa: ARG001
    """Very light noise — no structural bias."""
    return {
        "noise_scale": 0.8,
        "load_delta_percent": rng.gauss(0, 2.0),   # slight load variation
    }

