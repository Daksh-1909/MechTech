"""CLI entry point for the MechTech sensor simulator.

This is the Phase 1 scaffold. Reading generation and backend ingestion will be
added once the sensor-data contract and ingestion API are implemented (Phase 2).
"""

import argparse
from dataclasses import asdict

from simulator.config import SimulatorConfig
from simulator.scenarios import SCENARIO_RANGES, Scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mechtech-simulator",
        description="Generate simulated motor sensor readings (prototype only).",
    )
    parser.add_argument("--equipment-id", default="motor-001")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between readings.")
    parser.add_argument(
        "--scenario",
        choices=[scenario.value for scenario in Scenario],
        default=Scenario.NORMAL.value,
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--duration", type=float, default=None, help="Optional run duration.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = SimulatorConfig(
        equipment_id=args.equipment_id,
        backend_url=args.backend_url,
        interval_seconds=args.interval,
        scenario=Scenario(args.scenario),
        seed=args.seed,
        duration_seconds=args.duration,
    )

    print("MechTech simulator (simulated data - not a physical sensor)")
    for key, value in asdict(config).items():
        print(f"  {key}: {value}")

    if config.scenario in SCENARIO_RANGES:
        print(f"  ranges: {SCENARIO_RANGES[config.scenario]}")
    print("Reading generation is not implemented yet (Phase 2/3).")


if __name__ == "__main__":
    main()
