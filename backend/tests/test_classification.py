import numpy as np
import pytest

from app.core.exceptions import AppError
from app.ml.classification import predict_fault
from app.ml.datasets import SYNTHETIC_LABELS
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION


class _ScoresModel:
    classes_ = np.asarray(SYNTHETIC_LABELS)

    def __init__(self, scores: list[float]) -> None:
        self.scores = np.asarray(scores)

    def predict_proba(self, _matrix):
        return [self.scores]


def _bundle(scores: list[float], minimum_score: float = 0.4) -> dict:
    return {
        "artifact_type": "random_forest",
        "model": _ScoresModel(scores),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "labels": list(SYNTHETIC_LABELS),
        "minimum_score": minimum_score,
    }


def test_classifier_returns_unknown_when_evidence_is_weak() -> None:
    features = dict.fromkeys(FEATURE_NAMES, 1.0)
    predicted, scores, confidence, uncertain = predict_fault(
        _bundle([0.21] * 5),
        features,
    )

    assert predicted == "unknown"
    assert uncertain is True
    assert confidence == pytest.approx(0.21)
    assert set(scores) == set(SYNTHETIC_LABELS)


def test_classifier_returns_a_supported_label_when_score_clears_threshold() -> None:
    features = dict.fromkeys(FEATURE_NAMES, 1.0)
    predicted, _, confidence, uncertain = predict_fault(
        _bundle([0.05, 0.05, 0.8, 0.05, 0.05]),
        features,
    )
    assert predicted == "overheating"
    assert confidence == pytest.approx(0.8)
    assert uncertain is False


def test_classifier_rejects_invalid_threshold_and_missing_features() -> None:
    with pytest.raises(AppError) as threshold_error:
        predict_fault(
            _bundle([0.2] * 5),
            dict.fromkeys(FEATURE_NAMES, 1.0),
            minimum_score=1.1,
        )
    assert threshold_error.value.code == "INVALID_THRESHOLD"

    with pytest.raises(AppError) as feature_error:
        predict_fault(_bundle([0.2] * 5), {"count": 1.0})
    assert feature_error.value.code == "INVALID_FEATURES"
