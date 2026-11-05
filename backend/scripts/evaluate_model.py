"""Evaluate a trusted local model artifact against synthetic prototype windows."""

import argparse
import json
import sys
from pathlib import Path

import joblib

from app.core.time import utcnow
from app.db.session import SessionLocal
from app.ml.datasets import generate_synthetic_window_dataset
from app.ml.evaluation import classification_metrics
from app.ml.features import FEATURE_SCHEMA_VERSION
from app.ml.service import resolve_artifact_path
from app.models import ModelRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a local MechTech model artifact.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--artifact", help="Artifact path under DATA_ROOT/models.")
    source.add_argument("--model-id", type=int, help="Registered model id.")
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--window-size", type=int, default=12)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--output", help="Optional JSON report path.")
    parser.add_argument(
        "--update-registry",
        action="store_true",
        help="Update evaluation metrics for --model-id.",
    )
    return parser


def evaluate_artifact(
    artifact: Path,
    *,
    samples: int,
    window_size: int,
    seed: int,
) -> dict:
    features, labels, _ = generate_synthetic_window_dataset(
        samples=samples,
        seed=seed,
        window_size=window_size,
    )
    model = joblib.load(artifact)
    predictions = model.predict(features)
    metrics = classification_metrics(labels, predictions)
    metrics.update(
        {
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "evaluated_at": utcnow().isoformat(),
            "samples": samples,
            "window_size": window_size,
            "seed": seed,
            "artifact": str(artifact),
            "dataset_description": "Deterministic synthetic feature windows.",
        }
    )
    return metrics


def main() -> int:
    args = build_parser().parse_args()
    model_entry = None

    try:
        if args.model_id is not None:
            with SessionLocal() as db:
                model_entry = db.get(ModelRegistry, args.model_id)
                if model_entry is None:
                    print("Registered model was not found.", file=sys.stderr)
                    return 1
                artifact = resolve_artifact_path(model_entry.artifact_path)
                metrics = evaluate_artifact(
                    artifact,
                    samples=args.samples,
                    window_size=args.window_size,
                    seed=args.seed,
                )
                if args.update_registry:
                    model_entry.evaluation_metrics_json = metrics
                    db.commit()
        else:
            artifact = resolve_artifact_path(args.artifact)
            metrics = evaluate_artifact(
                artifact,
                samples=args.samples,
                window_size=args.window_size,
                seed=args.seed,
            )
    except (OSError, ValueError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1

    output = (
        Path(args.output) if args.output else artifact.with_name(f"{artifact.stem}.evaluation.json")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Artifact:  {artifact}")
    print(f"Report:    {output}")
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"F1 macro:  {metrics['f1_macro']:.4f}")
    if args.update_registry and model_entry is not None:
        print(f"Updated evaluation metrics for model id {model_entry.id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
