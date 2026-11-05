"""Deterministic, labeled simulator datasets for offline training/evaluation."""

import csv
import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from simulator.scenarios import PHASE3_LABELS, Scenario

PHASE3_SCENARIOS = tuple(Scenario(label) for label in PHASE3_LABELS)


def generate_dataset(
    *,
    samples_per_scenario: int,
    seed: int,
    equipment_id: str = "motor-001",
    run_prefix: str = "phase3",
    interval_seconds: float = 1.0,
    started_at: datetime = datetime(2026, 1, 1, tzinfo=UTC),
) -> list[dict[str, object]]:
    """Return reproducible canonical payloads; each scenario has a separate run ID."""
    if samples_per_scenario < 1:
        raise ValueError("samples_per_scenario must be positive.")
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive.")
    if started_at.tzinfo is None:
        raise ValueError("started_at must be timezone-aware.")

    from simulator.simulator import generate_contract_reading

    output: list[dict[str, object]] = []
    for scenario_index, scenario in enumerate(PHASE3_SCENARIOS):
        run_id = f"{run_prefix}-{scenario.value}-{seed}-{scenario_index}"
        rng = random.Random(seed + scenario_index * 1009)  # noqa: S311
        for _sequence in range(samples_per_scenario):
            stream_sequence = len(output)
            timestamp = started_at.astimezone(UTC) + timedelta(
                seconds=stream_sequence * interval_seconds
            )
            reading = generate_contract_reading(
                equipment_id=equipment_id,
                scenario=scenario,
                rng=rng,
                timestamp=timestamp,
                sequence=stream_sequence,
                seed=seed,
                run_id=run_id,
            )
            output.append(reading)
    return output


def export_csv(readings: list[dict[str, object]], path: Path) -> Path:
    """Export canonical payloads as flat CSV columns with JSON metadata fields."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "schema_version",
        "equipment_id",
        "timestamp",
        "sequence",
        "source",
        "temperature_c",
        "vibration_value",
        "vibration_unit",
        "speed_rpm",
        "load_percent",
        "scenario_id",
        "scenario_label",
        "simulation_seed",
        "simulation_run_id",
        "source_event_id",
    )
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for payload in readings:
            writer.writerow(
                {
                    "schema_version": payload["schema_version"],
                    "equipment_id": payload["equipment_id"],
                    "timestamp": payload["timestamp"],
                    "sequence": payload["sequence"],
                    "source": payload["source"],
                    "temperature_c": payload["temperature_c"],
                    "vibration_value": payload["vibration_value"],
                    "vibration_unit": payload["vibration_unit"],
                    "speed_rpm": payload["speed_rpm"],
                    "load_percent": payload["load_percent"],
                    "scenario_id": payload["scenario_id"],
                    "scenario_label": payload["scenario_label"],
                    "simulation_seed": payload["simulation_seed"],
                    "simulation_run_id": payload["simulation_run_id"],
                    "source_event_id": payload["source_event_id"],
                }
            )
    return path


def export_metadata(readings: list[dict[str, object]], path: Path, *, seed: int) -> Path:
    """Save reproducibility metadata beside a generated CSV."""
    metadata_path = path.with_suffix(path.suffix + ".metadata.json")
    metadata_path.write_text(
        json.dumps(
            {
                "dataset_version": "1.0",
                "seed": seed,
                "scenario_labels": [scenario.value for scenario in PHASE3_SCENARIOS],
                "samples": len(readings),
                "run_ids": sorted({str(row["simulation_run_id"]) for row in readings}),
                "synthetic_data": True,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return metadata_path
