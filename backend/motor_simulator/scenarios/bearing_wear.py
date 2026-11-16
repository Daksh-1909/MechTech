"""Bearing wear scenario — increasing vibration with mild temperature rise.

Simulates progressive deterioration of rolling-element bearings.
Vibration grows super-linearly as surface pitting develops; temperature
rises slightly due to increased friction.

Expected ranges (simulated only):
  temperature_c  : 55–85 °C (gradual rise)
  vibration_value: starts ~0.05, rises to 0.5–0.8 by step 200
"""

import random
import math
from typing import Any


SCENARIO_ID = "bearing_wear"
SCENARIO_LABEL = "bearing_abnormality"

# Vibration growth exponent (super-linear degradation curve)
_VIB_GROWTH_COEFFICIENT = 0.000012
_VIB_GROWTH_EXPONENT = 1.6


def perturbation(step: int, rng: random.Random) -> dict[str, Any]:
    """Models bearing wear as vibration growing with a power law."""
    vib_bias = _VIB_GROWTH_COEFFICIENT * (step ** _VIB_GROWTH_EXPONENT)
    # Slight thermal rise due to bearing friction
    temp_bias = 0.08 * math.sqrt(step) + rng.gauss(0, 0.4)
    return {
        "vibration_bias": vib_bias + abs(rng.gauss(0, 0.002 * step)),
        "temperature_bias": temp_bias,
        "noise_scale": 1.2,
    }

