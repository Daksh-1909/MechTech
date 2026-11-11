"""Tests for MotorPhysics and ReadingGenerator.

These tests are pure-Python and do not require a running API or database.
"""

import sys
from pathlib import Path

# Ensure the backend root is on the path
_BACKEND = Path(__file__).resolve().parents[2]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pytest
import random
import math

from simulator.motor.physics import MotorPhysics, MotorParameters, MotorState
from simulator.motor.generator import ReadingGenerator


# ---------------------------------------------------------------------------
# Physics model tests
# ---------------------------------------------------------------------------

class TestMotorPhysics:
    def setup_method(self):
        self.physics = MotorPhysics()
        self.rng = random.Random(42)

    def test_tick_returns_valid_channels(self):
        state, channels = self.physics.tick(MotorState(), self.rng)
        assert "temperature_c" in channels
        assert "vibration_value" in channels
        assert "vibration_unit" in channels
        assert channels["vibration_unit"] == "simulated_index"

    def test_temperature_is_finite(self):
        state = MotorState()
        for _ in range(100):
            state, channels = self.physics.tick(state, self.rng)
            assert math.isfinite(channels["temperature_c"])

    def test_vibration_non_negative(self):
        state = MotorState()
        for _ in range(50):
            state, channels = self.physics.tick(state, self.rng)
            assert channels["vibration_value"] >= 0.0

    def test_speed_bounded(self):
        state = MotorState()
        params = self.physics.params
        for _ in range(50):
            state, channels = self.physics.tick(state, self.rng)
            assert 0 <= channels["speed_rpm"] <= params.rated_speed_rpm * 1.1

    def test_determinism_same_seed(self):
        """Same seed always produces the same first channel values."""
        physics = MotorPhysics()

        rng1 = random.Random(99)
        _, ch1 = physics.tick(MotorState(), rng1)

        rng2 = random.Random(99)
        _, ch2 = physics.tick(MotorState(), rng2)

        assert ch1["temperature_c"] == ch2["temperature_c"]
        assert ch1["vibration_value"] == ch2["vibration_value"]

    def test_temperature_bias_increases_temperature(self):
        """Adding a positive temperature_bias should raise steady-state temp."""
        physics = MotorPhysics()
        rng_a = random.Random(1)
        rng_b = random.Random(1)
        state_a = MotorState(temperature_c=60.0)
        state_b = MotorState(temperature_c=60.0)

        # Run 20 steps with large positive bias vs no bias
        for _ in range(20):
            state_a, _ = physics.tick(state_a, rng_a, {"temperature_bias": 50.0, "noise_scale": 0})
            state_b, _ = physics.tick(state_b, rng_b, {"noise_scale": 0})

        assert state_a.temperature_c > state_b.temperature_c

    def test_vibration_bias_increases_vibration(self):
        """Adding a positive vibration_bias should increase vibration."""
        physics = MotorPhysics()
        rng_a = random.Random(2)
        rng_b = random.Random(2)
        state_a = MotorState()
        state_b = MotorState()

        for _ in range(10):
            state_a, _ = physics.tick(state_a, rng_a, {"vibration_bias": 0.5, "noise_scale": 0})
            state_b, _ = physics.tick(state_b, rng_b, {"noise_scale": 0})

        assert state_a.vibration_value > state_b.vibration_value


# ---------------------------------------------------------------------------
# Generator tests
# ---------------------------------------------------------------------------

class TestReadingGenerator:
    def _make_generator(self, **kwargs):
        defaults = dict(
            equipment_id="00000000-0000-0000-0000-000000000001",
            scenario_id="normal",
            scenario_label="normal",
            seed=0,
        )
        defaults.update(kwargs)
        return ReadingGenerator(**defaults)

    def test_stream_produces_readings(self):
        gen = self._make_generator()
        readings = list(gen.stream(max_steps=5))
        assert len(readings) == 5

    def test_reading_has_required_fields(self):
        gen = self._make_generator()
        reading = next(iter(gen.stream(max_steps=1)))
        required = {
            "equipment_id", "timestamp", "temperature_c", "vibration_value",
            "vibration_unit", "source", "source_event_id", "schema_version",
            "sequence_number", "scenario_id", "scenario_label",
            "simulation_seed", "simulation_run_id",
        }
        for key in required:
            assert key in reading, f"Missing key: {key}"

    def test_determinism_same_seed(self):
        """Same seed produces identical readings across two generator instances."""
        g1 = self._make_generator(seed=7)
        g2 = self._make_generator(seed=7)

        r1 = list(g1.stream(max_steps=10))
        r2 = list(g2.stream(max_steps=10))

        for a, b in zip(r1, r2):
            assert a["temperature_c"] == b["temperature_c"]
            assert a["vibration_value"] == b["vibration_value"]
            assert a["source_event_id"] == b["source_event_id"]

    def test_different_seeds_produce_different_values(self):
        g1 = self._make_generator(seed=0)
        g2 = self._make_generator(seed=1)
        r1 = list(g1.stream(max_steps=5))
        r2 = list(g2.stream(max_steps=5))
        # At least one reading should differ
        all_same = all(
            a["temperature_c"] == b["temperature_c"] and a["vibration_value"] == b["vibration_value"]
            for a, b in zip(r1, r2)
        )
        assert not all_same

    def test_sequence_numbers_monotonic(self):
        gen = self._make_generator()
        readings = list(gen.stream(max_steps=20))
        seq_nums = [r["sequence_number"] for r in readings]
        assert seq_nums == list(range(20))

    def test_equipment_id_in_readings(self):
        eq_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        gen = self._make_generator(equipment_id=eq_id)
        for r in gen.stream(max_steps=3):
            assert r["equipment_id"] == eq_id

    def test_source_event_id_unique(self):
        gen = self._make_generator(seed=0)
        readings = list(gen.stream(max_steps=50))
        event_ids = [r["source_event_id"] for r in readings]
        assert len(event_ids) == len(set(event_ids)), "source_event_ids should be unique"

    def test_vibration_values_non_negative(self):
        gen = self._make_generator()
        for r in gen.stream(max_steps=100):
            assert r["vibration_value"] >= 0.0, f"Negative vibration at step {r['sequence_number']}"


# ---------------------------------------------------------------------------
# Scenario range tests
# ---------------------------------------------------------------------------

class TestScenarioRanges:
    """Verify each scenario stays within plausible (but simulated) bounds.

    These tests confirm the physics model is configured to produce
    representative training data — not to prove real-world accuracy.
    """

    def _run_scenario(self, perturbation_fn, steps: int = 200, seed: int = 0):
        from simulator.motor.physics import MotorPhysics, MotorState

        import random as _random
        rng = _random.Random(seed)
        physics = MotorPhysics()
        state = MotorState()
        temps, vibs = [], []
        for step in range(steps):
            p = perturbation_fn(step, rng)
            state, channels = physics.tick(state, rng, p)
            temps.append(channels["temperature_c"])
            vibs.append(channels["vibration_value"])
        return temps, vibs

    def test_normal_temperature_range(self):
        from simulator.scenarios.normal import perturbation
        temps, vibs = self._run_scenario(perturbation, steps=300)
        assert min(temps) >= 30.0, "Normal temp should be above ambient"
        assert max(temps) <= 100.0, f"Normal temp should not overheat, got {max(temps):.1f}"

    def test_overheating_temperature_rises(self):
        from simulator.scenarios.overheating import perturbation
        temps, _ = self._run_scenario(perturbation, steps=200)
        # Later readings should be meaningfully hotter than early ones
        early_avg = sum(temps[:20]) / 20
        late_avg = sum(temps[-20:]) / 20
        assert late_avg > early_avg + 15.0, (
            f"Overheating scenario should show rising temp; early={early_avg:.1f} late={late_avg:.1f}"
        )

    def test_bearing_wear_vibration_rises(self):
        from simulator.scenarios.bearing_wear import perturbation
        _, vibs = self._run_scenario(perturbation, steps=200)
        early_avg = sum(vibs[:20]) / 20
        late_avg = sum(vibs[-20:]) / 20
        assert late_avg > early_avg * 2, (
            f"Bearing wear should show rising vibration; early={early_avg:.4f} late={late_avg:.4f}"
        )

    def test_combined_both_rise(self):
        from simulator.scenarios.combined import perturbation
        temps, vibs = self._run_scenario(perturbation, steps=200)
        early_temp_avg = sum(temps[:20]) / 20
        late_temp_avg = sum(temps[-20:]) / 20
        early_vib_avg = sum(vibs[:20]) / 20
        late_vib_avg = sum(vibs[-20:]) / 20
        assert late_temp_avg > early_temp_avg + 10.0, "Combined: temp should rise"
        assert late_vib_avg > early_vib_avg, "Combined: vibration should rise"

    def test_noisy_sensor_high_variance(self):
        from simulator.scenarios.noisy_sensor import perturbation
        from simulator.scenarios.normal import perturbation as normal_perturbation
        import statistics
        normal_temps, normal_vibs = self._run_scenario(normal_perturbation, steps=200, seed=5)
        noisy_temps, noisy_vibs = self._run_scenario(perturbation, steps=200, seed=5)
        # Noisy sensor should exhibit noticeably more variance
        assert statistics.stdev(noisy_temps) > statistics.stdev(normal_temps) * 1.5, (
            "Noisy sensor should have higher temperature variance than normal"
        )

