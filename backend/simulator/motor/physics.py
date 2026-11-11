"""Motor physics model for deterministic simulation.

Produces physically plausible (but entirely simulated) values for:
- Winding temperature (°C)
- Vibration magnitude (simulated_index)
- Rotational speed (RPM)
- Load percentage

All randomness is seeded so the same (seed, step) always yields the
same reading — essential for reproducible test scenarios.

WARNING: This is a simulation model only.  Values do NOT reflect any
real motor or real-world measurement.  Results must not be presented
as evidence of fault detection capability.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MotorState:
    """Running state of the simulated motor at a point in time."""

    temperature_c: float = 40.0      # Ambient + warm-up offset
    vibration_value: float = 0.05    # Healthy baseline (simulated_index)
    speed_rpm: float = 1480.0        # Near-synchronous 4-pole, 50 Hz
    load_percent: float = 70.0       # Moderate load


@dataclass
class MotorParameters:
    """Fixed nameplate / design values for the simulated motor."""

    rated_speed_rpm: float = 1480.0
    rated_load_percent: float = 100.0
    ambient_temperature_c: float = 25.0
    # Thermal rise at full load (°C above ambient)
    thermal_rise_at_full_load: float = 55.0
    # Coefficient: temperature rise per unit extra load above rated
    thermal_overload_coefficient: float = 0.6
    # Healthy RMS vibration at rated speed (simulated_index)
    vibration_baseline: float = 0.05
    # Natural vibration sensitivity to speed deviation (index / RPM)
    vibration_speed_sensitivity: float = 0.0003


class MotorPhysics:
    """Simulates one tick of motor physics given current state and perturbations.

    Usage::

        rng = random.Random(seed)
        physics = MotorPhysics(params=MotorParameters())
        state = MotorState()
        for step in range(n):
            perturbation = {...}  # from scenario
            new_state, channels = physics.tick(state, rng, perturbation)
            state = new_state
    """

    def __init__(self, params: MotorParameters | None = None) -> None:
        self.params = params or MotorParameters()

    def tick(
        self,
        state: MotorState,
        rng: random.Random,
        perturbation: dict[str, Any] | None = None,
    ) -> tuple[MotorState, dict[str, Any]]:
        """Advance state by one tick and return updated state + reading channels.

        ``perturbation`` keys (all optional):
        - ``speed_delta_rpm`` — shift target RPM
        - ``load_delta_percent`` — shift load
        - ``temperature_bias`` — additional temperature added
        - ``vibration_bias`` — additional vibration added
        - ``noise_scale`` — multiplier for noise amplitude (default 1.0)
        """
        p = perturbation or {}
        noise_scale = float(p.get("noise_scale", 1.0))

        # --- Speed ---
        target_rpm = self.params.rated_speed_rpm + float(p.get("speed_delta_rpm", 0.0))
        # First-order lag: speed tracks target slowly
        speed = state.speed_rpm + 0.3 * (target_rpm - state.speed_rpm)
        speed += rng.gauss(0, 1.5 * noise_scale)
        speed = max(0.0, min(speed, target_rpm * 1.1))

        # --- Load ---
        target_load = max(0.0, min(100.0, state.load_percent + float(p.get("load_delta_percent", 0.0))))
        load = state.load_percent + 0.2 * (target_load - state.load_percent)
        load += rng.gauss(0, 0.5 * noise_scale)
        load = max(0.0, min(100.0, load))

        # --- Temperature --- (thermal model: rise proportional to I²R ≈ load²)
        load_ratio = load / self.params.rated_load_percent
        # I²R losses scale with current squared; we approximate current ∝ load
        steady_state_temp = (
            self.params.ambient_temperature_c
            + self.params.thermal_rise_at_full_load * (load_ratio ** 2)
            + float(p.get("temperature_bias", 0.0))
        )
        # First-order thermal lag
        temp = state.temperature_c + 0.05 * (steady_state_temp - state.temperature_c)
        temp += rng.gauss(0, 0.3 * noise_scale)

        # --- Vibration --- (increases with speed deviation and load)
        speed_deviation = abs(speed - self.params.rated_speed_rpm)
        vib = (
            self.params.vibration_baseline
            + self.params.vibration_speed_sensitivity * speed_deviation
            + 0.001 * load_ratio
            + float(p.get("vibration_bias", 0.0))
        )
        vib = max(0.0, vib)
        # Multiplicative noise
        vib *= max(0.5, 1.0 + rng.gauss(0, 0.05 * noise_scale))

        new_state = MotorState(
            temperature_c=temp,
            vibration_value=vib,
            speed_rpm=speed,
            load_percent=load,
        )

        channels: dict[str, Any] = {
            "temperature_c": round(temp, 3),
            "vibration_value": round(vib, 5),
            "vibration_unit": "simulated_index",
            "speed_rpm": round(speed, 2),
            "load_percent": round(load, 2),
        }
        return new_state, channels

