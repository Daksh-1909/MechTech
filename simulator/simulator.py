"""CLI entry point for the MechTech sensor simulator.

Generates prototype temperature and vibration readings and sends them to the
MechTech ingestion API. Values are simulated, not physical measurements.
"""

import argparse
import json
import os
import random
import threading
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from simulator.config import SimulatorConfig
from simulator.dataset import export_csv, export_metadata, generate_dataset
from simulator.scenarios import NORMAL_RANGES, SCENARIO_RANGES, Scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mechtech-simulator",
        description="Generate and ingest simulated motor sensor readings (prototype only).",
    )
    parser.add_argument("--equipment-id", default="motor-001")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-prefix", default="/api/v1")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between readings.")
    parser.add_argument(
        "--scenario",
        choices=[scenario.value for scenario in Scenario],
        default=Scenario.NORMAL.value,
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--duration", type=float, default=None, help="Optional run duration.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of readings sent per request.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Send one reading, or one batch when --batch-size is greater than one.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("SIMULATOR_API_KEY"),
        help="Device API key (or set SIMULATOR_API_KEY).",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--export-csv",
        help="Generate a deterministic labeled CSV instead of sending readings to the API.",
    )
    parser.add_argument(
        "--samples-per-scenario",
        type=int,
        default=100,
        help="Readings per Phase 3 scenario when --export-csv is used.",
    )
    return parser


def generate_contract_reading(
    *,
    equipment_id: str,
    scenario: Scenario,
    rng: random.Random,
    timestamp: datetime,
    sequence: int,
    seed: int,
    run_id: str,
) -> dict[str, Any]:
    """Generate the versioned Phase 3 envelope, preserving normalized vibration units."""
    aliases = {
        Scenario.INCREASED_VIBRATION: Scenario.EXCESSIVE_VIBRATION,
    }
    label = aliases.get(scenario, scenario).value
    ranges = SCENARIO_RANGES.get(scenario, NORMAL_RANGES)
    temp_range = ranges["temperature_c"]
    vibration_range = ranges["vibration_normalized"]
    temperature = rng.uniform(*temp_range)
    vibration = rng.uniform(*vibration_range)
    if scenario == Scenario.BEARING_ABNORMALITY:
        # Vary the synthetic signal over time to model a scenario distinction,
        # without claiming a physical bearing-fault signature.
        vibration = min(1.0, vibration + 0.08 * abs(rng.gauss(0.0, 1.0)))
    observed_at = timestamp.astimezone(UTC)
    source_event_id = f"{equipment_id}:{run_id}:{sequence}"
    return {
        "schema_version": "1.0",
        "equipment_id": equipment_id,
        "timestamp": observed_at.isoformat().replace("+00:00", "Z"),
        "sequence": sequence,
        "source": "simulator",
        "source_event_id": source_event_id,
        "temperature_c": round(temperature, 3),
        "vibration_value": round(vibration, 4),
        "vibration_unit": "simulated_index",
        "speed_rpm": round(rng.uniform(1420.0, 1500.0), 1),
        "load_percent": round(rng.uniform(45.0, 85.0), 1),
        "scenario_id": run_id,
        "scenario_label": label,
        "simulation_seed": seed,
        "simulation_run_id": run_id,
    }


def generate_reading(
    config: SimulatorConfig,
    rng: random.Random,
    *,
    timestamp: datetime | None = None,
    sequence: int = 0,
    run_id: str | None = None,
) -> dict[str, Any] | None:
    if config.scenario == Scenario.SENSOR_DISCONNECTION:
        return None

    ranges = SCENARIO_RANGES.get(config.scenario, NORMAL_RANGES)
    temperature_low, temperature_high = ranges["temperature_c"]
    vibration_low, vibration_high = ranges["vibration_normalized"]
    temperature = rng.uniform(temperature_low, temperature_high)
    vibration = rng.uniform(vibration_low, vibration_high)
    quality_status = "valid"

    if config.scenario == Scenario.NOISY_SENSOR:
        temperature += rng.uniform(-2.0, 4.0)
        vibration += rng.uniform(-0.02, 0.05)
        if rng.random() < 0.25:
            quality_status = "partial"

    observed_at = timestamp or datetime.now(UTC)
    current_run_id = run_id or f"sim-{config.seed if config.seed is not None else 'live'}"
    scenario_label = {
        Scenario.INCREASED_VIBRATION: Scenario.EXCESSIVE_VIBRATION.value,
    }.get(config.scenario, config.scenario.value)
    return {
        "schema_version": "1.0",
        "equipment_id": config.equipment_id,
        "timestamp": observed_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "sequence": sequence,
        "source": config.source,
        "source_event_id": f"{config.equipment_id}:{current_run_id}:{sequence}",
        "temperature_c": round(temperature, 3),
        "vibration_value": round(max(0.0, vibration), 4),
        "vibration_unit": "simulated_index",
        "speed_rpm": round(rng.uniform(1420.0, 1500.0), 1),
        "load_percent": round(rng.uniform(45.0, 85.0), 1),
        "scenario_id": current_run_id,
        "scenario_label": scenario_label,
        "simulation_seed": config.seed,
        "simulation_run_id": current_run_id,
        "quality_status": quality_status,
    }


def _endpoint(config: SimulatorConfig, reading_count: int) -> str:
    suffix = "/readings/batch" if reading_count > 1 else "/readings"
    prefix = config.api_prefix.strip("/")
    path = f"/{prefix}/{suffix.lstrip('/')}" if prefix else suffix
    url = f"{config.backend_url.rstrip('/')}{path}"
    if urlparse(url).scheme not in {"http", "https"}:
        raise ValueError("The backend URL must use http or https.")
    return url


def send_readings(
    config: SimulatorConfig,
    readings: list[dict[str, Any]],
) -> dict[str, Any]:
    if not readings:
        return {}

    payload: dict[str, Any] = readings[0] if len(readings) == 1 else {"readings": readings}
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["X-Device-Key"] = config.api_key

    request = Request(  # noqa: S310
        _endpoint(config, len(readings)),
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    for attempt in range(1, config.max_retries + 1):
        try:
            with urlopen(  # noqa: S310
                request,
                timeout=config.request_timeout_seconds,
            ) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code < 500 or attempt == config.max_retries:
                raise RuntimeError(f"Ingestion failed with HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            if attempt == config.max_retries:
                raise RuntimeError(f"Ingestion failed: {exc.reason}") from exc

        time.sleep(min(2 ** (attempt - 1), 5))

    return {}


def run_simulation(
    config: SimulatorConfig,
    *,
    rng: random.Random | None = None,
    sender=send_readings,
    sleep=time.sleep,
    clock=time.monotonic,
    stop_event: threading.Event | None = None,
) -> int:
    rng = rng or random.Random(config.seed)  # noqa: S311
    run_id = uuid4().hex
    if config.once:
        batch = [
            reading
            for sequence in range(config.batch_size)
            if stop_event is None or not stop_event.is_set()
            if (reading := generate_reading(config, rng, sequence=sequence, run_id=run_id))
            is not None
        ]
        sender(config, batch)
        return len(batch)

    started = clock()
    deadline = None if config.duration_seconds is None else started + config.duration_seconds
    batch: list[dict[str, Any]] = []
    sent = 0

    while (deadline is None or clock() < deadline) and not (
        stop_event is not None and stop_event.is_set()
    ):
        reading = generate_reading(config, rng, sequence=sent + len(batch), run_id=run_id)
        if reading is not None:
            batch.append(reading)
            if len(batch) >= config.batch_size:
                sender(config, batch)
                sent += len(batch)
                batch = []

        remaining = None if deadline is None else deadline - clock()
        if remaining is not None and remaining <= 0:
            break
        sleep_seconds = (
            config.interval_seconds
            if remaining is None
            else min(config.interval_seconds, remaining)
        )
        sleep(sleep_seconds)

    if batch:
        sender(config, batch)
        sent += len(batch)
    return sent


def main() -> int:
    args = build_parser().parse_args()
    if args.export_csv:
        if args.seed is None:
            raise SystemExit("--export-csv requires --seed for reproducibility.")
        try:
            readings = generate_dataset(
                samples_per_scenario=args.samples_per_scenario,
                seed=args.seed,
                equipment_id=args.equipment_id,
                interval_seconds=args.interval,
            )
            path = export_csv(readings, Path(args.export_csv))
            metadata = export_metadata(readings, path, seed=args.seed)
        except (OSError, ValueError) as exc:
            raise SystemExit(f"Dataset export failed: {exc}") from exc
        print(f"Exported {len(readings)} simulated readings to {path}")
        print(f"Dataset metadata: {metadata}")
        return 0

    config = SimulatorConfig(
        equipment_id=args.equipment_id,
        backend_url=args.backend_url,
        api_prefix=args.api_prefix,
        interval_seconds=args.interval,
        scenario=Scenario(args.scenario),
        seed=args.seed,
        duration_seconds=args.duration,
        api_key=args.api_key,
        batch_size=args.batch_size,
        once=args.once,
        request_timeout_seconds=args.timeout,
    )

    print("MechTech simulator (simulated data - not a physical sensor)")
    for key, value in asdict(config).items():
        if "api_key" in key:
            value = "<configured>" if value else None
        print(f"  {key}: {value}")

    try:
        sent = run_simulation(config)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
        return 0
    except RuntimeError as exc:
        print(f"Simulator error: {exc}")
        return 1

    print(f"Sent {sent} simulated reading(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
