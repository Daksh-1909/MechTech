"""Measure bounded synthetic dataset and feature-pipeline cost locally."""

import argparse
import json
import platform
import sys
import time
import tracemalloc
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ml.datasets import generate_labeled_window_dataset  # noqa: E402
from app.ml.features import FEATURE_SCHEMA_VERSION  # noqa: E402


def run_benchmark(*, runs: int, samples: int, seed: int) -> dict:
    tracemalloc.start()
    started = time.perf_counter()
    rows = generate_labeled_window_dataset(
        run_seeds=list(range(seed, seed + runs)), samples_per_scenario=samples
    )
    elapsed = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # resource reports KiB on Linux and bytes on macOS. Windows has no module.
    try:
        import resource

        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    except (AttributeError, ImportError):
        peak_rss = None
    return {
        "runs": runs,
        "samples_per_scenario": samples,
        "feature_windows": len(rows),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "generation_and_features_seconds": round(elapsed, 6),
        "tracemalloc_peak_bytes": peak,
        "process_peak_rss_platform_units": peak_rss,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "synthetic_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--samples-per-scenario", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.runs <= 20 or not 40 <= args.samples_per_scenario <= 1000:
        parser.error("runs must be 1..20 and samples-per-scenario must be 40..1000")
    report = run_benchmark(runs=args.runs, samples=args.samples_per_scenario, seed=args.seed)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
