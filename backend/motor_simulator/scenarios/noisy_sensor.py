"""Noisy / degraded-sensor scenario.

Simulates a malfunctioning or poorly-calibrated sensor producing
high-amplitude random noise.  The underlying motor is healthy; only
the measurement quality is poor.

The ``quality_status`` field is set to ``"partial"`` for every reading
produced by this scenario so the ingestion layer can flag them.

Expected ranges (simulated only — noise dominates):
  temperature_c  : 25–110 °C (erratic)
  vibration_value: 0.0–0.9 (erratic)
"""

import random
from typing import Any


SCENARIO_ID = "noisy_sensor"
SCENARIO_LABEL = "normal"   # underlying motor state is normal

# Fraction of steps that produce a "spike" outlier
_SPIKE_PROBABILITY = 0.15


def perturbation(step: int, rng: random.Random) -> dict[str, Any]:  # noqa: ARG001
    """Inject large-amplitude noise; occasional spikes."""
    temp_spike = rng.gauss(0, 15.0) if rng.random() < _SPIKE_PROBABILITY else rng.gauss(0, 4.0)
    vib_spike = abs(rng.gauss(0, 0.2)) if rng.random() < _SPIKE_PROBABILITY else rng.gauss(0, 0.05)
    return {
        "temperature_bias": temp_spike,
        "vibration_bias": vib_spike,
        "noise_scale": 4.0,
    }

