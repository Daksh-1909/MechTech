from datetime import timedelta
from types import SimpleNamespace

import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.time import utcnow
from app.main import app
from app.ml.datasets import generate_labeled_window_dataset
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, build_features
from app.ml.service import resolve_artifact_path
from app.models import UserRole
from app.models.enums import ModelType
from app.modules.ml import service as ml_service
from scripts.train_random_forest import train_classifier
from tests.helpers import (
    create_user,
    csrf_headers,
    login,
    make_equipment,
    make_reading,
)


def test_feature_window_statistics_are_ordered_and_explicit() -> None:
    start = utcnow()
    readings = [
        SimpleNamespace(
            id=1,
            timestamp=start,
            temperature_c=50.0,
            vibration_value=0.1,
        ),
        SimpleNamespace(
            id=2,
            timestamp=start + timedelta(seconds=1),
            temperature_c=70.0,
            vibration_value=0.3,
        ),
        SimpleNamespace(
            id=3,
            timestamp=start + timedelta(seconds=2),
            temperature_c=None,
            vibration_value=0.5,
        ),
    ]

    features = build_features(readings)

    assert set(FEATURE_NAMES).issubset(features)
    assert features["count"] == 3.0
    assert features["temperature_mean"] == 60.0
    assert features["temperature_min"] == 50.0
    assert features["temperature_max"] == 70.0
    assert features["temperature_last"] == 70.0
    assert features["temperature_delta"] == 20.0
    assert features["vibration_mean"] == pytest.approx(0.3)
    assert features["vibration_delta"] == pytest.approx(0.4)


def test_artifact_paths_are_confined_to_the_model_directory(tmp_path) -> None:
    outside = tmp_path / "outside.joblib"
    outside.write_bytes(b"not-a-model")

    with pytest.raises(AppError) as exc_info:
        resolve_artifact_path(str(outside))
    assert exc_info.value.code == "ARTIFACT_PATH_INVALID"

    with pytest.raises(AppError) as missing:
        resolve_artifact_path("models/missing.joblib")
    assert missing.value.code == "ARTIFACT_MISSING"


def test_analysis_requires_model_and_persists_model_version(
    client: TestClient,
    db_session,
) -> None:
    make_equipment(db_session)
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    technician = create_user(
        db_session,
        email="tech@example.com",
        role=UserRole.TECHNICIAN,
    )
    csrf = login(client, technician.email)
    prefix = settings.api_v1_prefix

    no_data = client.post(
        f"{prefix}/equipment/motor-001/analysis",
        json={},
        headers=csrf_headers(csrf),
    )
    assert no_data.status_code == 409
    assert no_data.json()["error"]["code"] == "INSUFFICIENT_DATA"

    start = utcnow() - timedelta(minutes=2)
    make_reading(db_session, timestamp=start, temperature_c=48.0, vibration_value=0.15)
    make_reading(
        db_session,
        timestamp=start + timedelta(minutes=1),
        temperature_c=52.0,
        vibration_value=0.20,
    )

    unavailable = client.post(
        f"{prefix}/equipment/motor-001/analysis",
        json={},
        headers=csrf_headers(csrf),
    )
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "MODEL_UNAVAILABLE"

    models_dir = settings.data_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact = models_dir / "classifier.joblib"
    rows = []
    labels = []
    base = [0.0] * len(FEATURE_NAMES)
    for index in range(8):
        row = list(base)
        row[0] = 5.0 + index
        row[1] = 45.0 + index if index % 2 == 0 else 90.0 + index
        rows.append(row)
        labels.append("normal" if index % 2 == 0 else "overheating")
    model = LogisticRegression(max_iter=200).fit(rows, labels)
    joblib.dump(model, artifact)

    registered = ml_service.register_model(
        db_session,
        actor=admin,
        model_name="prototype-classifier",
        model_version="1.0.0",
        model_type=ModelType.CLASSIFICATION,
        artifact_path="models/classifier.joblib",
        training_dataset_description="Synthetic test data",
        evaluation_metrics_json={"accuracy": 1.0},
    )

    analyzed = client.post(
        f"{prefix}/equipment/motor-001/analysis",
        json={},
        headers=csrf_headers(csrf),
    )
    assert analyzed.status_code == 200, analyzed.text
    prediction = analyzed.json()
    assert prediction["model_registry_id"] == registered.id
    assert prediction["predicted_class"] in {"normal", "overheating"}
    assert prediction["confidence_value"] is not None
    assert set(prediction["probabilities_json"]) == {"normal", "overheating"}
    assert prediction["evidence_json"]["feature_schema_version"] == FEATURE_SCHEMA_VERSION
    assert prediction["evidence_json"]["window_size"] == 2

    listed = client.get(f"{prefix}/predictions", params={"equipment_id": "motor-001"})
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == prediction["id"]

    detail = client.get(f"{prefix}/predictions/{prediction['id']}")
    assert detail.status_code == 200
    assert detail.json()["model_registry_id"] == registered.id

    models = client.get(f"{prefix}/models")
    assert models.status_code == 200
    assert models.json()[0]["model_version"] == "1.0.0"

    operator = create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    with TestClient(app) as operator_client:
        login(operator_client, operator.email)
        forbidden_models = operator_client.get(f"{prefix}/models")
        assert forbidden_models.status_code == 403
        forbidden_analysis = operator_client.post(
            f"{prefix}/equipment/motor-001/analysis",
            json={},
            headers={
                settings.csrf_header_name: operator_client.cookies.get(settings.csrf_cookie_name)
            },
        )
        assert forbidden_analysis.status_code == 403


def test_analysis_handles_missing_active_artifact(client: TestClient, db_session) -> None:
    make_equipment(db_session)
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    technician = create_user(
        db_session,
        email="tech@example.com",
        role=UserRole.TECHNICIAN,
    )
    csrf = login(client, technician.email)
    prefix = settings.api_v1_prefix

    start = utcnow() - timedelta(minutes=2)
    make_reading(db_session, timestamp=start)
    make_reading(db_session, timestamp=start + timedelta(minutes=1))

    models_dir = settings.data_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact = models_dir / "deleted-after-registration.joblib"
    model = LogisticRegression(max_iter=200).fit(
        [[float(index)] * len(FEATURE_NAMES) for index in range(6)],
        ["normal", "normal", "normal", "fault", "fault", "fault"],
    )
    joblib.dump(model, artifact)
    ml_service.register_model(
        db_session,
        actor=admin,
        model_name="fragile-classifier",
        model_version="1.0.0",
        model_type=ModelType.CLASSIFICATION,
        artifact_path="models/deleted-after-registration.joblib",
        training_dataset_description=None,
        evaluation_metrics_json=None,
    )
    artifact.unlink()

    response = client.post(
        f"{prefix}/equipment/motor-001/analysis",
        json={},
        headers=csrf_headers(csrf),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ARTIFACT_MISSING"


def test_phase3_random_forest_can_be_explicitly_activated_and_used(
    client: TestClient,
    db_session,
) -> None:
    make_equipment(db_session)
    admin = create_user(db_session, email="admin-rf@example.com", role=UserRole.ADMIN)
    technician = create_user(db_session, email="tech-rf@example.com", role=UserRole.TECHNICIAN)
    start = utcnow() - timedelta(minutes=2)
    for index in range(12):
        make_reading(
            db_session,
            timestamp=start + timedelta(seconds=index),
            temperature_c=50.0 + index * 0.1,
            vibration_value=0.2 + index * 0.001,
            source_event_id=f"rf-analysis-{index}",
        )

    training_rows = generate_labeled_window_dataset(
        run_seeds=[71, 72],
        samples_per_scenario=40,
    )
    bundle, _ = train_classifier(training_rows, seed=71, minimum_score=0.4)
    models_dir = settings.data_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    artifact = models_dir / "phase3-random-forest.joblib"
    joblib.dump(bundle, artifact)
    registered = ml_service.register_model(
        db_session,
        actor=admin,
        model_name="phase3-random-forest",
        model_version="1.0.0",
        model_type=ModelType.CLASSIFICATION,
        artifact_path="models/phase3-random-forest.joblib",
        training_dataset_description="Run-separated test fixture",
        evaluation_metrics_json={"f1_macro": 1.0},
        training_dataset_version="1.0",
        activate=False,
    )
    assert registered.is_active is False
    active = ml_service.activate_model(db_session, actor=admin, model_entry=registered)
    assert active.is_active is True

    csrf = login(client, technician.email)
    response = client.post(
        f"{settings.api_v1_prefix}/equipment/motor-001/analysis",
        json={},
        headers=csrf_headers(csrf),
    )
    assert response.status_code == 200, response.text
    prediction = response.json()
    assert prediction["model_registry_id"] == registered.id
    assert prediction["predicted_class"] in {
        "normal",
        "excessive_vibration",
        "overheating",
        "bearing_abnormality",
        "combined_abnormality",
        "unknown",
    }
    assert isinstance(prediction["evidence_json"]["uncertain"], bool)
    assert isinstance(prediction["probabilities_json"], dict)
    assert "Random Forest class scores" in prediction["evidence_json"]["score_semantics"]
