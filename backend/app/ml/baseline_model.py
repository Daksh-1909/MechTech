"""Baseline Scikit-learn Classifier Training and Evaluation for Electric Motor Telemetry.

Trains a Random Forest classifier using synthetic deterministic feature windows
derived from the 4 motor simulation scenarios:
- normal
- overheating
- bearing_abnormality
- combined_abnormality

Adheres strictly to the architectural constraints:
- Uses synthetic deterministic data (seed-controlled).
- Clean separation between train and test runs to avoid leakage.
- Persists model artifact with provenance metadata and evaluation report.
- Produces calibrated class probability distributions and uncertainty markers.
"""

from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import Any
import uuid

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score

from app.core.config import settings
from app.ml.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    build_features,
    to_feature_vector,
)
from app.ml.service import models_root
from simulator.motor.generator import ReadingGenerator
from simulator.scenarios import (
    bearing_wear,
    combined,
    normal,
    overheating,
    PHASE3_LABELS,
)

logger = logging.getLogger(__name__)

SCENARIO_MAP = {
    "normal": (normal.perturbation, "normal"),
    "overheating": (overheating.perturbation, "overheating"),
    "bearing_wear": (bearing_wear.perturbation, "bearing_abnormality"),
    "combined": (combined.perturbation, "combined_abnormality"),
}


def generate_training_windows(
    run_seeds: list[int],
    samples_per_run: int = 40,
    window_size: int = 12,
) -> tuple[list[list[float]], list[str]]:
    """Generate non-overlapping feature windows from deterministic runs."""
    X: list[list[float]] = []
    y: list[str] = []

    for seed in run_seeds:
        for scenario_key, (pert_fn, label) in SCENARIO_MAP.items():
            gen = ReadingGenerator(
                equipment_id=f"train-eq-{seed}",
                scenario_id=scenario_key,
                scenario_label=label,
                seed=seed,
                interval_seconds=1.0,
            )
            raw_readings = list(gen.stream(perturbation_fn=pert_fn, max_steps=samples_per_run))

            # Segment into windows
            for i in range(0, len(raw_readings) - window_size + 1, window_size // 2):
                chunk = raw_readings[i : i + window_size]
                feats = build_features(chunk)
                vec = to_feature_vector(feats)
                X.append(vec)
                y.append(label)

    return X, y


def train_baseline_classifier(
    train_seeds: list[int] | None = None,
    test_seeds: list[int] | None = None,
    n_estimators: int = 50,
    random_state: int = 42,
) -> tuple[RandomForestClassifier, dict[str, Any], Path]:
    """Train, evaluate, and save the baseline motor fault classifier."""
    if train_seeds is None:
        train_seeds = [101, 102, 103, 104, 105]
    if test_seeds is None:
        test_seeds = [201, 202]

    # Generate train and test windows
    X_train, y_train = generate_training_windows(train_seeds, samples_per_run=60)
    X_test, y_test = generate_training_windows(test_seeds, samples_per_run=60)

    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=8,
        random_state=random_state,
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    rep = classification_report(y_test, y_pred, output_dict=True)

    metrics = {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "classification_report": rep,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "train_seeds": train_seeds,
        "test_seeds": test_seeds,
        "evaluated_at": datetime.now(UTC).isoformat(),
    }

    # Ensure models directory exists
    target_dir = models_root()
    target_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = target_dir / "motor_fault_classifier_v1.joblib"

    bundle = {
        "artifact_type": "random_forest",
        "model_key": "motor_fault_classifier",
        "version": "1.0.0",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "labels": list(PHASE3_LABELS),
        "model": clf,
        "metrics": metrics,
        "created_at": datetime.now(UTC).isoformat(),
    }

    joblib.dump(bundle, artifact_path)
    logger.info("Saved baseline classifier artifact to %s (Accuracy: %.3f)", artifact_path, acc)

    return clf, metrics, artifact_path


def predict_window(
    bundle: dict[str, Any],
    features: dict[str, float],
    minimum_confidence: float = 0.55,
) -> dict[str, Any]:
    """Inference function complying with versioned inference contract."""
    clf = bundle["model"]
    labels = bundle["labels"]

    vector = np.asarray([to_feature_vector(features)], dtype=np.float64)
    probs = clf.predict_proba(vector)[0]

    prob_map = {label: round(float(probs[i]), 4) for i, label in enumerate(clf.classes_)}
    top_idx = int(np.argmax(probs))
    top_class = str(clf.classes_[top_idx])
    confidence = float(probs[top_idx])

    is_uncertain = confidence < minimum_confidence

    return {
        "predicted_class": "uncertain" if is_uncertain else top_class,
        "raw_predicted_class": top_class,
        "confidence": round(confidence, 4),
        "is_uncertain": is_uncertain,
        "probabilities": prob_map,
        "model_version": bundle.get("version", "1.0.0"),
        "disclaimer": "Advisory ML prediction based on simulated feature windows. Not confirmed physical fault.",
    }

