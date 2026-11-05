"""Fit an explainable normal-only baseline and report held-out scenario behavior."""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulator.dataset import generate_dataset  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.paths import ensure_data_directories  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.ml.baseline import (  # noqa: E402
    activate_baseline,
    compare_features,
    fit_baseline,
    save_baseline,
)
from app.ml.features import segment_readings  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-scenario", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", default="normal-operation")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--z-threshold", type=float, default=None)
    parser.add_argument("--activate", action="store_true")
    parser.add_argument("--output", help="Optional JSON report output path.")
    return parser


def _windows_by_scenario(rows: list[dict]) -> dict[str, list]:
    grouped: dict[str, list[SimpleNamespace]] = defaultdict(list)
    labels: dict[str, str] = {}
    for index, row in enumerate(rows):
        run_id = str(row["simulation_run_id"])
        grouped[run_id].append(
            SimpleNamespace(
                id=index + 1,
                equipment_id=str(row["equipment_id"]),
                sequence_number=int(row["sequence"]),
                timestamp=datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00")),
                temperature_c=float(row["temperature_c"]),
                vibration_value=float(row["vibration_value"]),
            )
        )
        labels[run_id] = str(row["scenario_label"])

    result: dict[str, list] = defaultdict(list)
    for run_id, readings in grouped.items():
        result[labels[run_id]].extend(
            window for window in segment_readings(readings) if window.complete
        )
    return dict(result)


def train_and_report(args: argparse.Namespace) -> tuple[dict, Path]:
    ensure_data_directories()
    rows = generate_dataset(
        samples_per_scenario=args.samples_per_scenario,
        seed=args.seed,
    )
    windows_by_scenario = _windows_by_scenario(rows)
    normal_windows = windows_by_scenario.get("normal", [])
    if len(normal_windows) < 2:
        raise ValueError("The generated normal run did not produce enough complete windows.")
    threshold = args.z_threshold or settings.statistical_baseline_z_threshold
    baseline_values = fit_baseline(
        (window.features for window in normal_windows),
        scenario_labels=["normal"] * len(normal_windows),
        baseline_name=args.name,
        baseline_version=args.version,
        dataset_description=(
            f"Synthetic normal-only run; seed={args.seed}; "
            f"samples_per_scenario={args.samples_per_scenario}; dataset_version=1.0"
        ),
        z_threshold=threshold,
    )
    reference = SimpleNamespace(
        baseline_version=baseline_values["baseline_version"],
        feature_schema_version=baseline_values["feature_schema_version"],
        means_json=baseline_values["means_json"],
        standard_deviations_json=baseline_values["standard_deviations_json"],
        z_threshold=baseline_values["z_threshold"],
    )
    scenario_metrics = {}
    for scenario, windows in windows_by_scenario.items():
        detected = sum(
            compare_features(window.features, reference).is_anomaly for window in windows
        )
        scenario_metrics[scenario] = {
            "windows": len(windows),
            "flagged_windows": detected,
            "detection_rate": detected / len(windows) if windows else None,
        }

    with SessionLocal() as db:
        profile = save_baseline(db, baseline_values)
        if args.activate:
            activate_baseline(db, profile)
        profile_id = profile.id

    report = {
        "baseline_id": profile_id,
        "baseline_name": args.name,
        "baseline_version": args.version,
        "feature_schema_version": baseline_values["feature_schema_version"],
        "training_normal_windows": len(normal_windows),
        "seed": args.seed,
        "z_threshold": threshold,
        "scenarios": scenario_metrics,
        "limitations": "Synthetic scenarios only; not validated for physical motors.",
    }
    output = (
        Path(args.output)
        if args.output
        else settings.data_root / "exports" / f"baseline-{args.name}-{args.version}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report, output


def main() -> int:
    args = build_parser().parse_args()
    try:
        report, output = train_and_report(args)
    except Exception as exc:
        print(f"Baseline training failed: {exc}", file=sys.stderr)
        return 1
    print(f"Baseline report: {output}")
    print(f"Normal training windows: {report['training_normal_windows']}")
    for scenario, values in report["scenarios"].items():
        print(f"{scenario}: {values['flagged_windows']}/{values['windows']} flagged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
