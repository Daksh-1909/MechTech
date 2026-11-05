from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.time import utcnow
from app.ml.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    build_features,
    build_window,
    persist_window,
    segment_readings,
    to_feature_vector,
)
from app.models import FeatureWindow, SensorReading
from tests.helpers import make_equipment, make_reading


def _samples(count: int, *, missing_at: set[int] | None = None):
    start = utcnow() - timedelta(minutes=1)
    missing_at = missing_at or set()
    return [
        SimpleNamespace(
            id=index + 1,
            equipment_id="motor-001",
            sequence_number=index,
            timestamp=start
            + timedelta(seconds=index + (1 if index >= 5 and 5 in missing_at else 0)),
            temperature_c=50.0 + index,
            vibration_value=0.2 + index / 100,
        )
        for index in range(count)
    ]


def test_feature_schema_has_deterministic_statistics_and_no_default_filling() -> None:
    readings = _samples(10)
    features = build_features(readings)

    assert features["count"] == 10.0
    assert features["temperature_mean"] == 54.5
    assert features["temperature_median"] == 54.5
    expected_rms = (sum((50 + index) ** 2 for index in range(10)) / 10) ** 0.5
    assert features["temperature_rms"] == pytest.approx(expected_rms)
    assert features["temperature_peak_to_peak"] == 9.0
    assert features["temperature_slope_per_second"] == pytest.approx(1.0)
    assert features["vibration_mean"] == pytest.approx(0.245)
    assert len(to_feature_vector(features)) == len(FEATURE_NAMES)
    with pytest.raises(ValueError, match="missing required fields"):
        to_feature_vector({"count": 10.0})


def test_windows_report_gaps_insufficient_samples_and_stride() -> None:
    readings = _samples(15)
    windows = segment_readings(
        readings,
        window_seconds=10,
        stride_seconds=5,
        expected_interval_seconds=1,
        min_samples=8,
    )
    assert windows[0].complete is True
    assert windows[0].feature_schema_version == FEATURE_SCHEMA_VERSION
    assert windows[1].complete is True
    assert windows[2].complete is False
    assert windows[2].incomplete_reason == "insufficient_samples"

    gapped = _samples(10, missing_at={5})
    window = build_window(
        gapped,
        window_start=gapped[0].timestamp,
        window_seconds=10,
        expected_interval_seconds=1,
        min_samples=8,
    )
    assert window.complete is False
    assert window.gap_count == 1
    assert "missing_samples" in (window.incomplete_reason or "")
    assert window.features == {}


def test_feature_window_persistence_preserves_raw_readings(db_session) -> None:
    make_equipment(db_session)
    start = utcnow() - timedelta(minutes=1)
    rows = [
        make_reading(
            db_session,
            timestamp=start + timedelta(seconds=index),
            temperature_c=50 + index,
            vibration_value=0.2 + index / 100,
            source_event_id=f"feature-{index}",
        )
        for index in range(10)
    ]
    original = [(row.temperature_c, row.vibration_value) for row in rows]
    result = build_window(
        rows,
        window_start=start,
        window_seconds=10,
        expected_interval_seconds=1,
        min_samples=8,
    )
    persisted = persist_window(db_session, result)
    db_session.commit()

    stored = db_session.get(FeatureWindow, persisted.id)
    assert stored is not None
    assert stored.source_reading_ids_json == [row.id for row in rows]
    assert stored.feature_schema_version == FEATURE_SCHEMA_VERSION
    refreshed = list(db_session.scalars(select(SensorReading).order_by(SensorReading.id)))
    assert [(row.temperature_c, row.vibration_value) for row in refreshed] == original

    duplicate = persist_window(db_session, result)
    assert duplicate.id == persisted.id

    late_arrival = replace(
        result,
        sample_count=11,
        source_reading_ids=(*result.source_reading_ids, 999),
        features={**result.features, "temperature_mean": result.features["temperature_mean"] + 1},
    )
    revised_snapshot = persist_window(db_session, late_arrival)
    assert revised_snapshot.id != persisted.id
    assert stored.feature_values_json["temperature_mean"] == result.features["temperature_mean"]
