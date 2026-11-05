"""Train a prototype classification model outside the request path."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.core.paths import ensure_data_directories
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.ml.datasets import generate_synthetic_window_dataset
from app.ml.evaluation import classification_metrics
from app.ml.features import FEATURE_SCHEMA_VERSION
from app.ml.service import models_root
from app.models import UserRole
from app.models.enums import ModelType
from app.modules.auth import repository as auth_repository
from app.modules.auth.service import normalize_email
from app.modules.ml import service as ml_service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train and optionally register a local prototype model.",
    )
    parser.add_argument("--samples", type=int, default=400)
    parser.add_argument("--window-size", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-name", default="prototype-classifier")
    parser.add_argument("--model-version", default="1.0.0")
    parser.add_argument(
        "--output",
        default="models/classification/prototype-classifier-1.0.0.joblib",
    )
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--admin-email")
    return parser


def _resolve_output(raw_path: str) -> Path:
    path = Path(raw_path)
    resolved = path.resolve() if path.is_absolute() else (settings.data_root / path).resolve()
    if not resolved.is_relative_to(models_root()):
        raise ValueError("Model output must be inside DATA_ROOT/models.")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def train_model(
    *,
    samples: int,
    window_size: int,
    seed: int,
    output: Path,
) -> tuple[Path, dict[str, Any]]:
    features, labels, feature_names = generate_synthetic_window_dataset(
        samples=samples,
        seed=seed,
        window_size=window_size,
    )
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=seed,
        stratify=labels,
    )

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=seed),
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics = classification_metrics(y_test, predictions)
    metrics.update(
        {
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "feature_names": feature_names,
            "samples": samples,
            "window_size": window_size,
            "seed": seed,
            "trained_at": utcnow().isoformat(),
            "dataset_description": "Deterministic synthetic feature windows.",
            "limitations": (
                "Synthetic prototype data only. Scores are not calibrated real-world "
                "fault probabilities."
            ),
        }
    )

    joblib.dump(model, output)
    metrics_path = output.with_name(f"{output.stem}.metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    return metrics_path, metrics


def _register(
    *,
    artifact: Path,
    model_name: str,
    model_version: str,
    metrics: dict[str, Any],
    admin_email: str | None,
) -> int | None:
    if not admin_email:
        print("--register requires --admin-email.", file=sys.stderr)
        return None

    with SessionLocal() as db:
        admin = auth_repository.get_user_by_email(db, normalize_email(admin_email))
        if admin is None or admin.role != UserRole.ADMIN.value:
            print("An active administrator with that email was not found.", file=sys.stderr)
            return None

        relative_artifact = artifact.relative_to(settings.data_root).as_posix()
        entry = ml_service.register_model(
            db,
            actor=admin,
            model_name=model_name,
            model_version=model_version,
            model_type=ModelType.CLASSIFICATION,
            artifact_path=relative_artifact,
            training_dataset_description=str(metrics.get("dataset_description")),
            evaluation_metrics_json=metrics,
        )
        return entry.id


def main() -> int:
    args = build_parser().parse_args()
    ensure_data_directories()
    try:
        output = _resolve_output(args.output)
        metrics_path, metrics = train_model(
            samples=args.samples,
            window_size=args.window_size,
            seed=args.seed,
            output=output,
        )
    except (ValueError, OSError) as exc:
        print(f"Training failed: {exc}", file=sys.stderr)
        return 1

    print(f"Artifact: {output}")
    print(f"Metrics:  {metrics_path}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"F1 macro: {metrics['f1_macro']:.4f}")

    if args.register:
        model_id = _register(
            artifact=output,
            model_name=args.model_name,
            model_version=args.model_version,
            metrics=metrics,
            admin_email=args.admin_email,
        )
        if model_id is None:
            return 1
        print(f"Registered model id: {model_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
