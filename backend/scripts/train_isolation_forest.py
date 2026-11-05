"""Train/evaluate a run-separated Isolation Forest using synthetic normal windows."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings  # noqa: E402
from app.core.paths import ensure_data_directories  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ml.anomaly import score_window, train_isolation_forest  # noqa: E402
from app.ml.datasets import DATASET_VERSION, generate_labeled_window_dataset  # noqa: E402
from app.ml.evaluation import anomaly_metrics  # noqa: E402
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION  # noqa: E402
from app.ml.service import artifact_sha256, models_root  # noqa: E402
from app.models.enums import ModelType  # noqa: E402
from app.models.user import UserRole  # noqa: E402
from app.modules.auth import repository as auth_repository  # noqa: E402
from app.modules.auth.service import normalize_email  # noqa: E402
from app.modules.ml import service as ml_service  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-runs", type=int, default=6)
    parser.add_argument("--evaluation-runs", type=int, default=2)
    parser.add_argument("--samples-per-scenario", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--contamination", type=float, default=0.05)
    parser.add_argument("--model-name", default="isolation-forest")
    parser.add_argument("--model-version", default="1.0.0")
    parser.add_argument("--output", default="models/anomaly/isolation-forest-1.0.0.joblib")
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--admin-email")
    parser.add_argument("--report")
    return parser


def _resolve_output(raw_path: str) -> Path:
    path = Path(raw_path)
    root = models_root()
    resolved = path.resolve() if path.is_absolute() else (settings.data_root / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Model output must be inside DATA_ROOT/models.")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def train_and_evaluate(
    *,
    train_runs: int,
    evaluation_runs: int,
    samples_per_scenario: int,
    seed: int,
    contamination: float,
    output: Path,
    model_name: str = "isolation-forest",
    model_version: str = "1.0.0",
) -> tuple[Path, dict[str, Any]]:
    if train_runs < 2 or evaluation_runs < 1:
        raise ValueError("Use at least two training runs and one held-out evaluation run.")
    train_seeds = list(range(seed, seed + train_runs))
    evaluation_seeds = list(range(seed + 10_000, seed + 10_000 + evaluation_runs))
    training_rows = generate_labeled_window_dataset(
        run_seeds=train_seeds,
        samples_per_scenario=samples_per_scenario,
    )
    evaluation_rows = generate_labeled_window_dataset(
        run_seeds=evaluation_seeds,
        samples_per_scenario=samples_per_scenario,
    )
    normal_training = [row["features"] for row in training_rows if row["label"] == "normal"]
    if len(normal_training) < 10:
        raise ValueError("Training data produced fewer than ten normal windows.")

    started = time.perf_counter()
    bundle = train_isolation_forest(
        normal_training,
        seed=seed,
        contamination=contamination,
    )
    training_seconds = time.perf_counter() - started

    y_true: list[bool] = []
    y_pred: list[bool] = []
    inference_started = time.perf_counter()
    for row in evaluation_rows:
        result = score_window(bundle, row["features"], model_version=model_version)
        y_true.append(row["label"] != "normal")
        y_pred.append(result.is_anomaly)
    inference_seconds = time.perf_counter() - inference_started
    metrics = anomaly_metrics(y_true, y_pred)

    joblib.dump(bundle, output)
    checksum = artifact_sha256(output)
    report_path = output.with_name(f"{output.stem}.metrics.json")
    report = {
        "model_name": model_name,
        "model_version": model_version,
        "algorithm": "sklearn.ensemble.IsolationForest",
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "training_dataset_version": DATASET_VERSION,
        "training_run_seeds": train_seeds,
        "evaluation_run_seeds": evaluation_seeds,
        "run_sets_disjoint": not set(train_seeds).intersection(evaluation_seeds),
        "training_normal_windows": len(normal_training),
        "evaluation_windows": len(evaluation_rows),
        "contamination": contamination,
        "decision_rule": "IsolationForest.predict == -1; raw scores are not probabilities",
        "metrics": metrics,
        "training_seconds": training_seconds,
        "mean_inference_seconds_per_window": (
            inference_seconds / len(evaluation_rows) if evaluation_rows else None
        ),
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
            model_type=ModelType.ANOMALY,
            artifact_path=artifact.relative_to(settings.data_root).as_posix(),
            training_dataset_description="Run-separated synthetic normal/abnormal evaluation.",
            evaluation_metrics_json=report["metrics"],
            training_dataset_version=DATASET_VERSION,
            activate=activate,
        )
        return entry.id


def main() -> int:
    args = build_parser().parse_args()
    if args.activate and not args.register:
        print("--activate requires --register.", file=sys.stderr)
        return 2
    ensure_data_directories()
    try:
        artifact = _resolve_output(args.output)
        report_path, report = train_and_evaluate(
            train_runs=args.train_runs,
            evaluation_runs=args.evaluation_runs,
            samples_per_scenario=args.samples_per_scenario,
            seed=args.seed,
            contamination=args.contamination,
            output=artifact,
            model_name=args.model_name,
            model_version=args.model_version,
        )
    except (OSError, ValueError) as exc:
        print(f"Isolation Forest training failed: {exc}", file=sys.stderr)
        return 1
    print(f"Artifact: {artifact}")
    print(f"Metrics: {report_path}")
    print(f"F1: {report['metrics']['f1']:.4f}")
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
