"""Deterministic fixed-window feature extraction; raw readings are never modified."""

import math
import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.time import utcnow
from app.models import FeatureWindow, SensorReading

FEATURE_SCHEMA_VERSION = "2.0"
ROLLING_WINDOW_SAMPLES = 3


def _channel_feature_names(prefix: str) -> tuple[str, ...]:
    return (
        f"{prefix}_mean",
        f"{prefix}_median",
        f"{prefix}_std",
        f"{prefix}_min",
        f"{prefix}_max",
        f"{prefix}_rms",
        f"{prefix}_peak_to_peak",
        f"{prefix}_slope_per_second",
        f"{prefix}_rate_of_change",
        f"{prefix}_rolling_std",
    )


FEATURE_NAMES: tuple[str, ...] = (
    "count",
    *_channel_feature_names("temperature"),
    "temperature_last",
    "temperature_delta",
    *_channel_feature_names("vibration"),
    "vibration_last",
    "vibration_delta",
)

FEATURE_UNITS: dict[str, str] = {
    "count": "samples",
    "temperature_mean": "degC",
    "temperature_median": "degC",
    "temperature_std": "degC",
    "temperature_min": "degC",
    "temperature_max": "degC",
    "temperature_rms": "degC",
    "temperature_peak_to_peak": "degC",
    "temperature_slope_per_second": "degC/s",
    "temperature_rate_of_change": "degC/s",
    "temperature_rolling_std": "degC",
    "temperature_last": "degC",
    "temperature_delta": "degC",
    "vibration_mean": "simulated_index_or_declared_unit",
    "vibration_median": "simulated_index_or_declared_unit",
    "vibration_std": "simulated_index_or_declared_unit",
    "vibration_min": "simulated_index_or_declared_unit",
    "vibration_max": "simulated_index_or_declared_unit",
    "vibration_rms": "simulated_index_or_declared_unit",
    "vibration_peak_to_peak": "simulated_index_or_declared_unit",
    "vibration_slope_per_second": "declared_unit/s",
    "vibration_rate_of_change": "declared_unit/s",
    "vibration_rolling_std": "simulated_index_or_declared_unit",
    "vibration_last": "simulated_index_or_declared_unit",
    "vibration_delta": "simulated_index_or_declared_unit",
}


@dataclass(frozen=True, slots=True)
class WindowFeatures:
    equipment_id: str
    window_start: datetime
    window_end: datetime
    sample_count: int
    source_reading_ids: tuple[int, ...]
    features: dict[str, float]
    feature_schema_version: str
    gap_count: int
    irregular_interval_count: int
    complete: bool
    incomplete_reason: str | None


def _ordered(readings: Iterable[SensorReading]) -> list[SensorReading]:
    return sorted(
        readings,
        key=lambda reading: (
            reading.timestamp,
            getattr(reading, "sequence_number", None)
            if getattr(reading, "sequence_number", None) is not None
            else getattr(reading, "id", 0),
            getattr(reading, "id", 0),
        ),
    )


def _channel_values(readings: list[SensorReading], name: str) -> list[tuple[datetime, float]]:
    return [
        (reading.timestamp, float(value))
        for reading in readings
        if (value := getattr(reading, name)) is not None
    ]


def _slope(points: list[tuple[datetime, float]]) -> float:
    if len(points) < 2:
        return 0.0
    origin = points[0][0]
    x = [(timestamp - origin).total_seconds() for timestamp, _ in points]
    y = [value for _, value in points]
    mean_x = statistics.fmean(x)
    mean_y = statistics.fmean(y)
    denominator = sum((value - mean_x) ** 2 for value in x)
    if denominator == 0:
        return 0.0
    return (
        sum((x_value - mean_x) * (y_value - mean_y) for x_value, y_value in zip(x, y, strict=True))
        / denominator
    )


def _rolling_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    width = min(ROLLING_WINDOW_SAMPLES, len(values))
    return max(
        statistics.pstdev(values[index : index + width]) for index in range(len(values) - width + 1)
    )


def _channel_features(points: list[tuple[datetime, float]], prefix: str) -> dict[str, float]:
    values = [value for _, value in points]
    if not values:
        return {}
    mean = statistics.fmean(values)
    slope = _slope(points)
    result = {
        f"{prefix}_mean": mean,
        f"{prefix}_median": statistics.median(values),
        f"{prefix}_std": statistics.pstdev(values) if len(values) > 1 else 0.0,
        f"{prefix}_min": min(values),
        f"{prefix}_max": max(values),
        f"{prefix}_last": values[-1],
        f"{prefix}_delta": values[-1] - values[0],
        f"{prefix}_rms": math.sqrt(statistics.fmean(value * value for value in values)),
        f"{prefix}_peak_to_peak": max(values) - min(values),
        f"{prefix}_slope_per_second": slope,
        f"{prefix}_rate_of_change": slope,
        f"{prefix}_rolling_std": _rolling_std(values),
    }
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError("Feature extraction produced a non-finite value.")
    return result


def build_features(readings: Iterable[SensorReading]) -> dict[str, float]:
    """Build the Phase 3.0 feature vector for one ordered collection of readings."""
    ordered = _ordered(readings)
    if not ordered:
        raise ValueError("At least one reading is required to calculate features.")
    features: dict[str, float] = {"count": float(len(ordered))}
    features.update(_channel_features(_channel_values(ordered, "temperature_c"), "temperature"))
    features.update(_channel_features(_channel_values(ordered, "vibration_value"), "vibration"))
    return features


def to_feature_vector(features: dict[str, float]) -> list[float]:
    missing = [name for name in FEATURE_NAMES if name not in features]
    if missing:
        raise ValueError(f"Feature vector is missing required fields: {', '.join(missing)}")
    vector = [float(features[name]) for name in FEATURE_NAMES]
    if not all(math.isfinite(value) for value in vector):
        raise ValueError("Feature vector contains non-finite values.")
    return vector


def _interval_quality(
    readings: list[SensorReading],
    expected_interval_seconds: float,
) -> tuple[int, int]:
    gaps = 0
    irregular = 0
    tolerance = max(expected_interval_seconds * 0.1, 0.05)
    for previous, current in zip(readings, readings[1:], strict=False):
        elapsed = (current.timestamp - previous.timestamp).total_seconds()
        if elapsed > expected_interval_seconds * 1.5:
            gaps += max(1, round(elapsed / expected_interval_seconds) - 1)
        if abs(elapsed - expected_interval_seconds) > tolerance:
            irregular += 1
    return gaps, irregular


def build_window(
    readings: Iterable[SensorReading],
    *,
    window_start: datetime,
    window_seconds: float | None = None,
    expected_interval_seconds: float | None = None,
    min_samples: int | None = None,
) -> WindowFeatures:
    """Calculate one fixed window and mark gaps/insufficient cadence explicitly."""
    duration = window_seconds or settings.feature_window_seconds
    interval = expected_interval_seconds or settings.feature_sample_interval_seconds
    minimum = min_samples or settings.feature_min_samples
    window_end = window_start + timedelta(seconds=duration)
    selected = [
        reading for reading in _ordered(readings) if window_start <= reading.timestamp < window_end
    ]
    gaps, irregular = _interval_quality(selected, interval)
    reasons: list[str] = []
    expected_samples = max(1, math.floor(duration / interval))
    if len(selected) < minimum or len(selected) < expected_samples:
        reasons.append("insufficient_samples")
    if gaps:
        reasons.append("missing_samples")
    if irregular:
        reasons.append("irregular_intervals")
    complete = not reasons
    features = build_features(selected) if complete else {}
    equipment_id = selected[0].equipment_id if selected else ""
    return WindowFeatures(
        equipment_id=equipment_id,
        window_start=window_start,
        window_end=window_end,
        sample_count=len(selected),
        source_reading_ids=tuple(int(reading.id) for reading in selected),
        features=features,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        gap_count=gaps,
        irregular_interval_count=irregular,
        complete=complete,
        incomplete_reason=",".join(reasons) if reasons else None,
    )


def segment_readings(
    readings: Iterable[SensorReading],
    *,
    window_seconds: float | None = None,
    stride_seconds: float | None = None,
    expected_interval_seconds: float | None = None,
    min_samples: int | None = None,
) -> list[WindowFeatures]:
    ordered = _ordered(readings)
    if not ordered:
        return []
    duration = window_seconds or settings.feature_window_seconds
    stride = stride_seconds or settings.feature_stride_seconds
    if duration <= 0 or stride <= 0:
        raise ValueError("Window duration and stride must be positive.")
    starts: list[datetime] = []
    cursor = ordered[0].timestamp
    last = ordered[-1].timestamp
    while cursor <= last:
        starts.append(cursor)
        cursor += timedelta(seconds=stride)
    return [
        build_window(
            ordered,
            window_start=start,
            window_seconds=duration,
            expected_interval_seconds=expected_interval_seconds,
            min_samples=min_samples,
        )
        for start in starts
    ]


def persist_window(db: Session, window: WindowFeatures) -> FeatureWindow:
    if not window.equipment_id:
        raise AppError(
            "Cannot persist an empty feature window.", code="EMPTY_WINDOW", status_code=400
        )
    existing = db.scalar(
        select(FeatureWindow).where(
            FeatureWindow.equipment_id == window.equipment_id,
            FeatureWindow.window_start == window.window_start,
            FeatureWindow.feature_schema_version == window.feature_schema_version,
        )
    )
    if existing is not None:
        existing.window_end = window.window_end
        existing.sample_count = window.sample_count
        existing.feature_values_json = window.features
        existing.source_reading_ids_json = list(window.source_reading_ids)
        existing.incomplete_reason = window.incomplete_reason
        db.flush()
        return existing
    stored = FeatureWindow(
        equipment_id=window.equipment_id,
        window_start=window.window_start,
        window_end=window.window_end,
        sample_count=window.sample_count,
        feature_schema_version=window.feature_schema_version,
        feature_values_json=window.features,
        source_reading_ids_json=list(window.source_reading_ids),
        incomplete_reason=window.incomplete_reason,
        created_at=utcnow(),
    )
    db.add(stored)
    db.flush()
    return stored
