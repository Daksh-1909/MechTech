from datetime import UTC, datetime, timedelta

import joblib
import pytest

from app.core.config import settings
from app.core.exceptions import AppError
from app.ml.anomaly import (
    AnomalyResult,
    persist_anomaly_event,
    score_window,
    train_isolation_forest,
)
from app.ml.features import FEATURE_NAMES
from app.ml.service import artifact_sha256, load_registered_artifact
from app.models import FeatureWindow, UserRole
from app.models.enums import ModelType
from app.modules.ml import service as ml_service
from tests.helpers import create_user, make_equipment


def _normal_rows(count: int = 30) -> list[dict[str, float]]:
    rows = []
    for sample in range(count):
        row = {}
        for index, name in enumerate(FEATURE_NAMES):
            base = 10.0 if name == "count" else 0.0
            row[name] = base + sample * 0.001 + index * 0.01
        rows.append(row)
    return rows


def test_isolation_forest_scores_and_reports_feature_deviations() -> None:
    training = _normal_rows()
    bundle = train_isolation_forest(training, seed=42, contamination=0.05)
    normal = score_window(bundle, training[0], model_version="1.0.0")

    unusual = dict(training[-1])
    unusual["temperature_mean"] += 100.0
    outlier = score_window(bundle, unusual, model_version="1.0.0")
    assert normal.detector_name == "isolation_forest"
    assert outlier.model_version == "1.0.0"
    assert isinstance(outlier.is_anomaly, bool)
    assert outlier.evidence["score_semantics"].startswith("raw Isolation Forest")
    assert outlier.evidence["top_feature_deviations"][0]["feature"] in FEATURE_NAMES


def test_invalid_anomaly_feature_schema_is_rejected() -> None:
    bundle = train_isolation_forest(_normal_rows(), seed=42)
    with pytest.raises(AppError) as exc_info:
        score_window(bundle, {"count": 30.0}, model_version="1.0.0")
    assert exc_info.value.code == "INVALID_FEATURES"


def test_registered_artifact_checksum_is_verified_before_loading(
    db_session,
    tmp_path,
    monkeypatch,
) -> None:
    make_equipment(db_session)
    actor = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    monkeypatch.setattr(settings, "data_root", tmp_path)
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    artifact = model_dir / "detector.joblib"
    joblib.dump({"safe": True}, artifact)
    entry = ml_service.register_model(
        db_session,
        actor=actor,
        model_name="detector",
        model_version="1.0.0",
        model_type=ModelType.ANOMALY,
        artifact_path="models/detector.joblib",
        training_dataset_description="test fixture",
        evaluation_metrics_json={},
        training_dataset_version="1.0",
        activate=False,
    )
    assert entry.is_active is False
    assert entry.artifact_sha256 == artifact_sha256(artifact)
    assert load_registered_artifact(entry) == {"safe": True}

    artifact.write_bytes(b"tampered")
    with pytest.raises(AppError) as exc_info:
        load_registered_artifact(entry)
    assert exc_info.value.code == "ARTIFACT_CHECKSUM_INVALID"


def test_isolation_forest_event_persists_window_and_model_provenance(db_session) -> None:
    make_equipment(db_session)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    window = FeatureWindow(
        equipment_id="motor-001",
        window_start=start,
        window_end=start + timedelta(seconds=10),
        sample_count=10,
        feature_schema_version="2.0",
        feature_values_json={},
        source_reading_ids_json=[1, 2, 3],
    )
    db_session.add(window)
    db_session.flush()
    result = AnomalyResult(
        is_anomaly=True,
        score=-0.3,
        decision_threshold=0.0,
        detector_name="isolation_forest",
        model_version="1.0.0",
        evidence={"decision_score": -0.1},
    )
    event = persist_anomaly_event(
        db_session,
        equipment_id="motor-001",
        feature_window_id=window.id,
        window_start=start,
        window_end=start + timedelta(seconds=10),
        result=result,
    )
    db_session.commit()
    assert event is not None
    assert event.feature_window_id == window.id
    assert event.detector_name == "isolation_forest"
    assert event.model_version == "1.0.0"
    assert event.evidence_json["decision_score"] == -0.1


def test_model_registration_does_not_activate_until_validated(
    db_session, tmp_path, monkeypatch
) -> None:
    make_equipment(db_session)
    actor = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    monkeypatch.setattr(settings, "data_root", tmp_path)
    artifact_dir = tmp_path / "models"
    artifact_dir.mkdir()
    artifact_path = artifact_dir / "detector.joblib"
    joblib.dump(train_isolation_forest(_normal_rows(), seed=7), artifact_path)
    entry = ml_service.register_model(
        db_session,
        actor=actor,
        model_name="activation-test",
        model_version="1.0.0",
        model_type=ModelType.ANOMALY,
        artifact_path="models/detector.joblib",
        training_dataset_description="test fixture",
        evaluation_metrics_json={},
        training_dataset_version="1.0",
        activate=False,
    )
    assert entry.is_active is False
    activated = ml_service.activate_model(db_session, actor=actor, model_entry=entry)
    assert activated.is_active is True
