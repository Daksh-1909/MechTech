import statistics
from collections.abc import Iterable

from app.models import SensorReading

FEATURE_SCHEMA_VERSION = "1.0"

FEATURE_NAMES: tuple[str, ...] = (
    "count",
    "temperature_mean",
    "temperature_std",
    "temperature_min",
    "temperature_max",
    "temperature_last",
    "temperature_delta",
    "vibration_mean",
    "vibration_std",
    "vibration_min",
    "vibration_max",
    "vibration_last",
    "vibration_delta",
)


def _channel_statistics(values: list[float], prefix: str) -> dict[str, float]:
    if not values:
        return {
            f"{prefix}_mean": 0.0,
            f"{prefix}_std": 0.0,
            f"{prefix}_min": 0.0,
            f"{prefix}_max": 0.0,
            f"{prefix}_last": 0.0,
            f"{prefix}_delta": 0.0,
        }

    return {
        f"{prefix}_mean": statistics.fmean(values),
        f"{prefix}_std": statistics.pstdev(values) if len(values) > 1 else 0.0,
        f"{prefix}_min": min(values),
        f"{prefix}_max": max(values),
        f"{prefix}_last": values[-1],
        f"{prefix}_delta": values[-1] - values[0],
    }


def build_features(readings: Iterable[SensorReading]) -> dict[str, float]:
    ordered = sorted(readings, key=lambda reading: (reading.timestamp, reading.id))
    temperatures = [
        float(reading.temperature_c) for reading in ordered if reading.temperature_c is not None
    ]
    vibrations = [
        float(reading.vibration_value) for reading in ordered if reading.vibration_value is not None
    ]

    features: dict[str, float] = {"count": float(len(ordered))}
    features.update(_channel_statistics(temperatures, "temperature"))
    features.update(_channel_statistics(vibrations, "vibration"))
    return features


def to_feature_vector(features: dict[str, float]) -> list[float]:
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]
