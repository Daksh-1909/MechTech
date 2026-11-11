"""Combined abnormality scenario — simultaneous temperature and vibration faults.

Simulates a severe degradation event where both cooling failure and
mechanical imbalance occur together (e.g. bearing failure causing
rotor imbalance with inadequate cooling).

Expected ranges (simulated only):
  temperature_c  : rises to 110–150 °C
  vibration_value: rises to 0.6–1.0
"""

import random
import math
from typing import Any


SCENARIO_ID = "combined_abnormality"
SCENARIO_LABEL = "combined_abnormality"

_TEMP_RAMP = 0.25
_VIB_GROWTH = 0.000015
_VIB_EXP = 1.5


def perturbation(step: int, rng: random.Random) -> dict[str, Any]:
    """Both temperature and vibration escalate together."""
    temp_bias = step * _TEMP_RAMP + rng.gauss(0, 1.0)
    vib_bias = _VIB_GROWTH * (step ** _VIB_EXP) + abs(rng.gauss(0, 0.003 * math.sqrt(step)))
    return {
        "temperature_bias": temp_bias,
        "vibration_bias": vib_bias,
        "load_delta_percent": rng.gauss(5, 3),   # running over-loaded
        "noise_scale": 1.5,
    }

