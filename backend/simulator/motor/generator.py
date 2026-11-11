"""Deterministic reading generator.

Combines MotorPhysics with a Scenario to produce a stream of
ReadingCreateRequest-compatible dicts, one per time step.

Design goals:
- Reproducible: same seed → same sequence
- Bounded: values stay within configured limits
- Traceable: every reading carries scenario_id, seed, and sequence_number
"""

import random
import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any

from simulator.motor.physics import MotorParameters, MotorPhysics, MotorState


class ReadingGenerator:
    """Generates dicts compatible with ReadingCreateRequest for a given scenario.

    Parameters
    ----------
    equipment_id:
        UUID of the target equipment record.
    scenario_id:
        Short identifier for the fault scenario (e.g. ``"normal"``).
    scenario_label:
        Human-readable label stored in the reading (must be one of the
        ReadingCreateRequest allowed values).
    sensor_id:
        Optional sensor UUID to attach to the generated readings.
    seed:
        Deterministic seed. The same seed always produces the same readings.
    start_time:
        Timestamp for the first reading (UTC). Defaults to now.
    interval_seconds:
        Time between readings.
    source:
        ``source`` field value (default ``"simulator"``).
    run_id:
        Unique run identifier stored in every reading; auto-generated if None.
    params:
        Motor nameplate parameters.
    """

    def __init__(
        self,
        *,
        equipment_id: str | uuid.UUID,
        scenario_id: str,
        scenario_label: str,
        sensor_id: str | uuid.UUID | None = None,
        seed: int = 0,
        start_time: datetime | None = None,
        interval_seconds: float = 5.0,
        source: str = "simulator",
        run_id: str | None = None,
        params: MotorParameters | None = None,
    ) -> None:
        self.equipment_id = str(equipment_id)
        self.scenario_id = scenario_id
        self.scenario_label = scenario_label
        self.sensor_id = str(sensor_id) if sensor_id else None
        self.seed = seed
        self.start_time = start_time or datetime.now(UTC)
        self.interval = timedelta(seconds=interval_seconds)
        self.source = source
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self.physics = MotorPhysics(params=params)

    def stream(
        self,
        perturbation_fn: Callable[[int, random.Random], dict[str, Any]] | None = None,
        max_steps: int | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Yield reading dicts indefinitely (or up to ``max_steps``).

        ``perturbation_fn`` is called each step with ``(step, rng)`` and
        returns a perturbation dict (see ``MotorPhysics.tick``).
        """
        rng = random.Random(self.seed)
        state = MotorState()
        step = 0
        timestamp = self.start_time

        while max_steps is None or step < max_steps:
            perturbation = perturbation_fn(step, rng) if perturbation_fn else {}
            state, channels = self.physics.tick(state, rng, perturbation)

            # Build a source_event_id that is deterministic per (run, step)
            event_id = f"{self.run_id}-{step:08d}"

            item: dict[str, Any] = {
                "equipment_id": self.equipment_id,
                "timestamp": timestamp.isoformat(),
                "recorded_at": timestamp.isoformat(),
                "temperature_c": channels["temperature_c"],
                "vibration_value": channels["vibration_value"],
                "vibration_unit": channels["vibration_unit"],
                "speed_rpm": channels["speed_rpm"],
                "load_percent": channels["load_percent"],
                "source": self.source,
                "source_event_id": event_id,
                "idempotency_key": event_id,
                "schema_version": "1.0",
                "sequence_number": step,
                "scenario_id": self.scenario_id,
                "scenario_label": self.scenario_label,
                "simulation_seed": self.seed,
                "simulation_run_id": self.run_id,
            }
            if self.sensor_id:
                item["sensor_id"] = self.sensor_id

            yield item

            timestamp += self.interval
            step += 1

