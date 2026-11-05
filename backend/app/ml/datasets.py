import random
from datetime import timedelta
from types import SimpleNamespace

from app.core.time import utcnow
from app.ml.features import FEATURE_NAMES, build_features, to_feature_vector

SYNTHETIC_LABELS: tuple[str, ...] = (
    "normal",
    "high_vibration",
    "overheating",
    "combined_abnormality",
)

_LABEL_RANGES: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {
    "normal": ((45.0, 60.0), (0.10, 0.30)),
    "high_vibration": ((45.0, 62.0), (0.65, 1.00)),
    "overheating": ((85.0, 110.0), (0.10, 0.30)),
    "combined_abnormality": ((85.0, 110.0), (0.65, 1.00)),
}


def generate_synthetic_window_dataset(
    *,
    samples: int,
    seed: int,
    window_size: int,
) -> tuple[list[list[float]], list[str], list[str]]:
    if samples < 1:
        raise ValueError("samples must be at least one.")
    if window_size < 2:
        raise ValueError("window_size must be at least two.")

    rng = random.Random(seed)  # noqa: S311
    started = utcnow() - timedelta(seconds=window_size)
    features: list[list[float]] = []
    labels: list[str] = []

    for index in range(samples):
        label = SYNTHETIC_LABELS[index % len(SYNTHETIC_LABELS)]
        temperature_range, vibration_range = _LABEL_RANGES[label]
        readings = [
            SimpleNamespace(
                id=index * window_size + offset + 1,
                timestamp=started + timedelta(seconds=offset),
                temperature_c=rng.uniform(*temperature_range),
                vibration_value=rng.uniform(*vibration_range),
            )
            for offset in range(window_size)
        ]
        window_features = build_features(readings)
        features.append(to_feature_vector(window_features))
        labels.append(label)

    return features, labels, list(FEATURE_NAMES)
