"""Evaluate a trusted classifier on independent labeled simulation runs."""

import argparse
import json
import sys
from pathlib import Path

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.time import utcnow  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ml.datasets import DATASET_VERSION, generate_labeled_window_dataset  # noqa: E402
from app.ml.evaluation import classification_metrics  # noqa: E402
from app.ml.features import FEATURE_NAMES, FEATURE_SCHEMA_VERSION, to_feature_vector  # noqa: E402
from app.ml.service import load_registered_artifact, resolve_artifact_path  # noqa: E402
from app.models import ModelRegistry  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--artifact", help="Artifact path under DATA_ROOT/models.")
    source.add_argument("--model-id", type=int, help="Registered model id.")
    parser.add_argument("--samples-per-scenario", type=int, default=120)
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--output", help="Optional JSON report path.")
    parser.add_argument("--update-registry", action="store_true")
    return parser


def evaluate_artifact(
    artifact: Path,
    *,
    samples: int,
    window_size: int,
    seed: int,
) -> dict:
    bundle = joblib.load(artifact)
    if not isinstance(bundle, dict) or bundle.get("artifact_type") != "random_forest":
        raise ValueError("Artifact is not a Phase 3 Random Forest bundle.")
    if bundle.get("feature_schema_version") != FEATURE_SCHEMA_VERSION:
        raise ValueError("Artifact feature schema does not match the current feature schema.")
    if bundle.get("feature_names") != list(FEATURE_NAMES):
        raise ValueError("Artifact feature ordering is invalid.")
    if bundle.get("labels") is None:
        raise ValueError("Artifact label metadata is missing.")

    run_count = max(1, min(5, samples // 10))
    run_count = max(run_count, 2)
    evaluation_seeds = list(range(seed + 10_000, seed + 10_000 + run_count))
    training_seeds = set(bundle.get("training_run_seeds", []))
    while training_seeds.intersection(evaluation_seeds):
        evaluation_seeds = [value + 10_000 for value in evaluation_seeds]
    rows = generate_labeled_window_dataset(
        run_seeds=evaluation_seeds,
        samples_per_scenario=max(40, samples, window_size * 4),
    )
    matrix = [to_feature_vector(row["features"]) for row in rows]
    labels = [row["label"] for row in rows]
    predictions = bundle["model"].predict(matrix)
    report = classification_metrics(labels, predictions)
    report.update(
        {
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "evaluated_at": utcnow().isoformat(),
            "dataset_version": DATASET_VERSION,
            "evaluation_seeds": evaluation_seeds,
            "evaluation_run_ids": sorted({row["run_id"] for row in rows}),
            "run_sets_disjoint_from_training": not training_seeds.intersection(evaluation_seeds),
            "limitations": "Synthetic scenarios only; not validated for physical motors.",
        }
    )
    return report


def main() -> int:
    args = build_parser().parse_args()
    if args.update_registry and args.model_id is None:
        print("--update-registry requires --model-id.", file=sys.stderr)
        return 2
    model_entry = None
    try:
        if args.model_id is not None:
            with SessionLocal() as db:
                model_entry = db.get(ModelRegistry, args.model_id)
                if model_entry is None:
                    print("Registered model was not found.", file=sys.stderr)
                    return 1
                bundle = load_registered_artifact(model_entry)
                artifact = resolve_artifact_path(model_entry.artifact_path)
                if not isinstance(bundle, dict) or bundle.get("artifact_type") != "random_forest":
                    raise ValueError("Registered model is not a Phase 3 Random Forest bundle.")
                report = evaluate_artifact(
                    artifact,
                    samples=args.samples_per_scenario,
                    window_size=10,
                    seed=args.seed,
                )
                if args.update_registry:
                    model_entry.evaluation_metrics_json = report
                    db.commit()
        else:
            artifact = resolve_artifact_path(args.artifact)
            report = evaluate_artifact(
                artifact,
                samples=args.samples_per_scenario,
                window_size=10,
                seed=args.seed,
            )
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1

    output = (
        Path(args.output) if args.output else artifact.with_name(f"{artifact.stem}.evaluation.json")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Artifact: {artifact}")
    print(f"Report: {output}")
    print(f"Accuracy: {report['accuracy']:.4f}")
    print(f"F1 macro: {report['f1_macro']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
