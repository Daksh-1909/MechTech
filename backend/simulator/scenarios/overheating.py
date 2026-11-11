"""Overheating scenario — gradual, sustained temperature rise.

Simulates a motor running with inadequate cooling or excessive ambient
temperature.  Temperature climbs slowly over time while vibration and
speed remain near normal.

Expected ranges (simulated only):
  temperature_c  : starts ~60 °C, rises to 110–130 °C over ~200 steps
  vibration_value: 0.04–0.15 (slight thermal expansion effect)
"""

import random
from typing import Any


SCENARIO_ID = "overheating"
SCENARIO_LABEL = "overheating"

# Degrees of temperature bias added per step (°C/step)
_TEMP_RAMP_RATE = 0.35


def perturbation(step: int, rng: random.Random) -> dict[str, Any]:
    """Ramps temperature bias linearly; vibration unaffected."""
    temperature_bias = step * _TEMP_RAMP_RATE + rng.gauss(0, 0.5)
    return {
        "temperature_bias": temperature_bias,
        "noise_scale": 1.0,
    }

