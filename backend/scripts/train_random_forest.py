"""Train/evaluate a five-class Random Forest with simulation-run isolation."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import joblib
from sklearn.ensemble import RandomForestClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.paths import ensure_data_directories  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ml.datasets import (  # noqa: E402
    DATASET_VERSION,
    SYNTHETIC_LABELS,
    generate_labeled_window_dataset,
    split_run_seeds,
)
from app.ml.evaluation import classification_metrics  # noqa: E402
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, to_feature_vector  # noqa: E402
from app.ml.service import artifact_sha256, models_root  # noqa: E402
from app.models.enums import ModelType  # noqa: E402
from app.models.user import UserRole  # noqa: E402
from app.modules.auth import repository as auth_repository  # noqa: E402
from app.modules.auth.service import normalize_email  # noqa: E402
from app.modules.ml import service as ml_service  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=8, help="Independent runs used for training.")
    parser.add_argument("--test-runs", type=int, default=2)
    parser.add_argument("--samples-per-scenario", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--minimum-score", type=float, default=0.4)
    parser.add_argument("--model-name", default="random-forest-fault-classifier")
    parser.add_argument("--model-version", default="1.0.0")
    parser.add_argument(
        "--output",
        default="models/classification/random-forest-fault-classifier-1.0.0.joblib",
    )
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--admin-email")
    parser.add_argument("--report")
    return parser


def _resolve_output(raw_path: str) -> Path:
    path = Path(raw_path)
    resolved = path.resolve() if path.is_absolute() else (settings.data_root / path).resolve()
    if not resolved.is_relative_to(models_root()):
        raise ValueError("Model output must be inside DATA_ROOT/models.")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def train_classifier(
    training_rows: list[dict],
    *,
    seed: int,
    minimum_score: float,
) -> tuple[dict[str, Any], float]:
    labels_seen = {row["label"] for row in training_rows}
    if labels_seen != set(SYNTHETIC_LABELS):
        raise ValueError("Training partition must contain every supported label.")
    matrix = [to_feature_vector(row["features"]) for row in training_rows]
    targets = [row["label"] for row in training_rows]
    start = time.perf_counter()
    model = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=1,
    )
    model.fit(matrix, targets)
    training_seconds = time.perf_counter() - start
    return (
        {
            "artifact_type": "random_forest",
            "model": model,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "feature_names": list(FEATURE_NAMES),
            "labels": list(SYNTHETIC_LABELS),
            "training_dataset_version": DATASET_VERSION,
            "minimum_score": minimum_score,
            "seed": seed,
        },
        training_seconds,
    )


def train_and_evaluate(
    *,
    runs: int,
    test_runs: int,
    samples_per_scenario: int,
    seed: int,
    minimum_score: float,
    output: Path,
    model_name: str = "random-forest-fault-classifier",
    model_version: str = "1.0.0",
) -> tuple[Path, dict[str, Any]]:
    if runs < 2 or test_runs < 1:
        raise ValueError("Use at least two training runs and one held-out test run.")
    if not 0 <= minimum_score <= 1:
        raise ValueError("minimum_score must be between zero and one.")
    seeds = list(range(seed, seed + runs + test_runs))
    training_seeds, testing_seeds = split_run_seeds(
        seeds,
        test_fraction=test_runs / len(seeds),
        random_state=seed,
    )
    training_rows = generate_labeled_window_dataset(
        run_seeds=training_seeds,
        samples_per_scenario=samples_per_scenario,
    )
    test_rows = generate_labeled_window_dataset(
        run_seeds=testing_seeds,
        samples_per_scenario=samples_per_scenario,
    )
    train_run_ids = {str(row["run_id"]) for row in training_rows}
    test_run_ids = {str(row["run_id"]) for row in test_rows}
    if train_run_ids.intersection(test_run_ids):
        raise ValueError("Train and test windows share a simulation run.")
    if {row["label"] for row in test_rows} != set(SYNTHETIC_LABELS):
        raise ValueError("Test partition must contain every supported label.")

    bundle, training_seconds = train_classifier(
        training_rows,
        seed=seed,
        minimum_score=minimum_score,
    )
    bundle["training_run_seeds"] = training_seeds
    bundle["training_run_ids"] = sorted(train_run_ids)
    x_test = [to_feature_vector(row["features"]) for row in test_rows]
    y_test = [row["label"] for row in test_rows]
    start = time.perf_counter()
    predictions = bundle["model"].predict(x_test)
    probabilities = bundle["model"].predict_proba(x_test)
    inference_seconds = time.perf_counter() - start
    metrics = classification_metrics(y_test, predictions)
    metrics.update(
        {
            "training_runs": len(training_seeds),
            "test_runs": len(testing_seeds),
            "run_sets_disjoint": train_run_ids.isdisjoint(test_run_ids),
            "training_seconds": training_seconds,
            "mean_inference_seconds_per_window": inference_seconds / len(test_rows),
        }
    )
    metrics["per_class_scores"] = {
        label: float(
            sum(
                probabilities[row_index][list(bundle["model"].classes_).index(label)]
                for row_index, target in enumerate(y_test)
                if target == label
            )
            / max(1, y_test.count(label))
        )
        for label in SYNTHETIC_LABELS
    }

    joblib.dump(bundle, output)
    checksum = artifact_sha256(output)
    report_path = output.with_name(f"{output.stem}.metrics.json")
    report = {
        "model_name": model_name,
        "model_version": model_version,
        "algorithm": "sklearn.ensemble.RandomForestClassifier",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "labels": list(SYNTHETIC_LABELS),
        "training_dataset_version": DATASET_VERSION,
        "training_seeds": training_seeds,
        "test_seeds": testing_seeds,
        "training_run_ids": sorted(train_run_ids),
        "test_run_ids": sorted(test_run_ids),
        "run_sets_disjoint": train_run_ids.isdisjoint(test_run_ids),
        "training_windows": len(training_rows),
        "test_windows": len(test_rows),
        "minimum_score_for_known_label": minimum_score,
        "scores_are_calibrated_probabilities": False,
        "metrics": metrics,
        "training_seconds": training_seconds,
        "mean_inference_seconds_per_window": inference_seconds / len(test_rows),
        "artifact_sha256": checksum,
        "seed": seed,
        "limitations": "Synthetic scenarios only; not validated for physical motors.",
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report_path, report


def _register(
    *,
    artifact: Path,
    report: dict[str, Any],
    admin_email: str | None,
    activate: bool,
) -> int | None:
    if not admin_email:
        print("--register requires --admin-email.", file=sys.stderr)
        return None
    with SessionLocal() as db:
        admin = auth_repository.get_user_by_email(db, normalize_email(admin_email))
        if admin is None or admin.role != UserRole.ADMIN.value:
            print("An active administrator with that email was not found.", file=sys.stderr)
            return None
        entry = ml_service.register_model(
            db,
            actor=admin,
            model_name=report["model_name"],
            model_version=report["model_version"],
            model_type=ModelType.CLASSIFICATION,
            artifact_path=artifact.relative_to(settings.data_root).as_posix(),
            training_dataset_description="Run-separated labeled synthetic simulation data.",
            evaluation_metrics_json=report["metrics"],
            training_dataset_version=DATASET_VERSION,
            activate=False,
        )
        if activate:
            ml_service.activate_model(db, actor=admin, model_entry=entry)
        return entry.id


def train_model(
    *,
    samples: int,
    window_size: int,
    seed: int,
    output: Path,
) -> tuple[Path, dict[str, Any]]:
    """Compatibility function retained for scripts/tests that imported Phase 2 training."""
    runs = 4
    report_path, report = train_and_evaluate(
        runs=runs,
        test_runs=1,
        samples_per_scenario=max(40, samples, window_size * 4),
        seed=seed,
        minimum_score=0.4,
        output=output,
    )
    return report_path, report["metrics"]


def main() -> int:
    args = build_parser().parse_args()
    if args.activate and not args.register:
        print("--activate requires --register.", file=sys.stderr)
        return 2
    ensure_data_directories()
    try:
        artifact = _resolve_output(args.output)
        report_path, report = train_and_evaluate(
            runs=args.runs,
            test_runs=args.test_runs,
            samples_per_scenario=args.samples_per_scenario,
            seed=args.seed,
            minimum_score=args.minimum_score,
            output=artifact,
            model_name=args.model_name,
            model_version=args.model_version,
        )
    except (OSError, ValueError) as exc:
        print(f"Random Forest training failed: {exc}", file=sys.stderr)
        return 1
    print(f"Artifact: {artifact}")
    print(f"Metrics: {report_path}")
    print(f"Accuracy: {report['metrics']['accuracy']:.4f}")
    print(f"F1 macro: {report['metrics']['f1_macro']:.4f}")
    if args.register:
        model_id = _register(
            artifact=artifact,
            report=report,
            admin_email=args.admin_email,
            activate=args.activate,
        )
        if model_id is None:
            return 1
        print(f"Registered model id: {model_id}; active={args.activate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
