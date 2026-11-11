"""Direct unit tests for the 5 motor simulation scenarios.

Verifies that each scenario perturbation function behaves deterministically
and adheres to the expected physical trends.
"""

import random
from simulator.scenarios import (
    bearing_wear,
    combined,
    noisy_sensor,
    normal,
    overheating,
)


def test_normal_scenario_perturbation():
    rng = random.Random(42)
    p = normal.perturbation(0, rng)
    assert "noise_scale" in p
    assert p["noise_scale"] == 0.8
    assert "load_delta_percent" in p


def test_overheating_scenario_rises():
    rng = random.Random(42)
    p0 = overheating.perturbation(0, rng)
    p100 = overheating.perturbation(100, rng)
    assert p100["temperature_bias"] > p0["temperature_bias"]


def test_bearing_wear_scenario_vibration_grows():
    rng = random.Random(42)
    p0 = bearing_wear.perturbation(0, rng)
    p100 = bearing_wear.perturbation(100, rng)
    assert p100["vibration_bias"] > p0["vibration_bias"]


def test_combined_scenario_both_escalate():
    rng = random.Random(42)
    p0 = combined.perturbation(0, rng)
    p100 = combined.perturbation(100, rng)
    assert p100["temperature_bias"] > p0["temperature_bias"]
    assert p100["vibration_bias"] > p0["vibration_bias"]


def test_noisy_sensor_scenario_perturbation():
    rng = random.Random(42)
    p = noisy_sensor.perturbation(0, rng)
    assert p["noise_scale"] == 4.0
    assert "temperature_bias" in p
    assert "vibration_bias" in p

