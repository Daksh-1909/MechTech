"""Reproducible synthetic windows with scenario-run provenance for ML workflows."""

import random
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from simulator.dataset import generate_dataset
from simulator.scenarios import PHASE3_LABELS, SCENARIO_RANGES, Scenario

from app.ml.features import FEATURE_NAMES, build_features, segment_readings, to_feature_vector

SYNTHETIC_LABELS = PHASE3_LABELS
DATASET_VERSION = "1.0"


def split_run_seeds(
    seeds: list[int],
    *,
    test_fraction: float = 0.25,
    random_state: int = 42,
) -> tuple[list[int], list[int]]:
    """Partition complete simulation runs before generating any windows."""
    unique = list(dict.fromkeys(seeds))
    if len(unique) < 2:
        raise ValueError("At least two distinct run seeds are required for a held-out split.")
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between zero and one.")
    shuffled = list(unique)
    random.Random(random_state).shuffle(shuffled)  # noqa: S311
    test_count = max(1, round(len(shuffled) * test_fraction))
    test_seeds = shuffled[:test_count]
    train_seeds = shuffled[test_count:]
    if not train_seeds:
        raise ValueError("The run split left no training runs.")
    return train_seeds, test_seeds


def generate_labeled_window_dataset(
    *,
    run_seeds: list[int],
    samples_per_scenario: int = 120,
) -> list[dict]:
    """Generate non-overlapping run partitions and then derive versioned windows."""
    if not run_seeds:
        raise ValueError("At least one run seed is required.")
    output: list[dict] = []
    reading_id = 0
    for seed in run_seeds:
        raw = generate_dataset(
            samples_per_scenario=samples_per_scenario,
            seed=seed,
            run_prefix=f"dataset-{seed}",
        )
        by_run: dict[str, list[SimpleNamespace]] = defaultdict(list)
        run_labels: dict[str, str] = {}
        for row in raw:
            reading_id += 1
            run_id = str(row["simulation_run_id"])
            by_run[run_id].append(
                SimpleNamespace(
                    id=reading_id,
                    equipment_id=str(row["equipment_id"]),
                    sequence_number=int(row["sequence"]),
                    timestamp=datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00")),
                    temperature_c=float(row["temperature_c"]),
                    vibration_value=float(row["vibration_value"]),
                )
            )
            run_labels[run_id] = str(row["scenario_label"])
        for run_id, readings in by_run.items():
            for window in segment_readings(readings):
                if not window.complete:
                    continue
                output.append(
                    {
                        "features": window.features,
                        "label": run_labels[run_id],
                        "run_id": run_id,
                        "seed": seed,
                        "window_start": window.window_start.isoformat(),
                        "window_end": window.window_end.isoformat(),
                        "source_reading_ids": list(window.source_reading_ids),
                    }
                )
    return output


def generate_synthetic_window_dataset(
    *,
    samples: int,
    seed: int,
    window_size: int,
) -> tuple[list[list[float]], list[str], list[str]]:
    """Small compatibility fixture generator; production scripts use run-level splits."""
    if samples < 1:
        raise ValueError("samples must be at least one.")
    if window_size < 2:
        raise ValueError("window_size must be at least two.")

    rng = random.Random(seed)  # noqa: S311
    features: list[list[float]] = []
    labels: list[str] = []
    for index in range(samples):
        label = SYNTHETIC_LABELS[index % len(SYNTHETIC_LABELS)]
        scenario = Scenario(label)
        ranges = SCENARIO_RANGES[scenario]
        temperature_range = ranges["temperature_c"]
        vibration_range = ranges["vibration_normalized"]
        started = datetime(2026, 1, 1, tzinfo=UTC)
        readings = [
            SimpleNamespace(
                id=index * window_size + offset + 1,
                equipment_id="motor-001",
                sequence_number=offset,
                timestamp=started + timedelta(seconds=offset),
                temperature_c=rng.uniform(*temperature_range),
                vibration_value=rng.uniform(*vibration_range),
            )
            for offset in range(window_size)
        ]
        features.append(to_feature_vector(build_features(readings)))
        labels.append(label)
    return features, labels, list(FEATURE_NAMES)
