"""Motor simulator runner.

Sends simulated motor readings to the MechTech API.

Usage::

    python -m simulator.runner \\
        --equipment-id <uuid> \\
        --scenario overheating \\
        --seed 42 \\
        --interval-seconds 1 \\
        --max-steps 60

Environment variables (or .env):
    SIM_API_BASE_URL   — API root (default http://localhost:8000/api/v1)
    SIM_API_KEY        — X-Device-Key header (optional)
    SIM_EQUIPMENT_ID   — target equipment UUID
    SIM_SCENARIO       — scenario name
    SIM_SEED           — random seed (default 42)
    SIM_INTERVAL_SECONDS — seconds between readings
    SIM_MAX_STEPS      — stop after N readings
    SIM_DRY_RUN        — if "true", print readings without sending

IMPORTANT: This simulator generates fictitious data for development and
academic demonstration purposes only.  Outputs must not be presented as
evidence of real-world fault detection capability.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure the backend package is importable when runner is called directly
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from simulator.config import SimulatorConfig  # noqa: E402
from simulator.motor.generator import ReadingGenerator  # noqa: E402

logger = logging.getLogger("mechtech.simulator")

# ---------------------------------------------------------------------------
# Scenario registry
# ---------------------------------------------------------------------------

_SCENARIOS: dict[str, Any] = {}


def _load_scenarios() -> None:
    from simulator.scenarios import normal, overheating, bearing_wear, combined, noisy_sensor

    _SCENARIOS["normal"] = normal.perturbation
    _SCENARIOS["overheating"] = overheating.perturbation
    _SCENARIOS["bearing_wear"] = bearing_wear.perturbation
    _SCENARIOS["combined"] = combined.perturbation
    _SCENARIOS["noisy_sensor"] = noisy_sensor.perturbation


_SCENARIO_LABELS: dict[str, str] = {
    "normal": "normal",
    "overheating": "overheating",
    "bearing_wear": "bearing_abnormality",
    "combined": "combined_abnormality",
    "noisy_sensor": "normal",
}


# ---------------------------------------------------------------------------
# HTTP client (stdlib only — no extra dependencies)
# ---------------------------------------------------------------------------


def _send_reading(
    base_url: str,
    payload: dict[str, Any],
    api_key: str | None,
    timeout: float,
) -> tuple[int, dict[str, Any]]:
    """POST a reading to /readings.  Returns (status_code, response_body)."""
    import http.client
    import urllib.parse

    url = f"{base_url}/readings"
    parsed = urllib.parse.urlsplit(url)
    host = parsed.netloc
    path = parsed.path

    body = json.dumps(payload).encode()
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["X-Device-Key"] = api_key

    is_https = parsed.scheme == "https"
    conn_cls = http.client.HTTPSConnection if is_https else http.client.HTTPConnection
    conn = conn_cls(host, timeout=timeout)
    try:
        conn.request("POST", path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"raw": raw.decode(errors="replace")}
        return resp.status, data
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run(config: SimulatorConfig) -> None:
    _load_scenarios()

    if config.scenario not in _SCENARIOS:
        available = ", ".join(sorted(_SCENARIOS))
        raise ValueError(f"Unknown scenario '{config.scenario}'. Available: {available}")

    perturbation_fn = _SCENARIOS[config.scenario]
    scenario_label = _SCENARIO_LABELS[config.scenario]

    generator = ReadingGenerator(
        equipment_id=config.equipment_id,
        scenario_id=config.scenario,
        scenario_label=scenario_label,
        seed=config.seed,
        start_time=datetime.now(UTC),
        interval_seconds=config.interval_seconds,
        source="simulator",
    )

    logger.info(
        "Simulator starting | equipment=%s scenario=%s seed=%d dry_run=%s",
        config.equipment_id,
        config.scenario,
        config.seed,
        config.dry_run,
    )

    wall_start = time.monotonic()
    step = 0

    for reading in generator.stream(
        perturbation_fn=perturbation_fn,
        max_steps=config.max_steps,
    ):
        if config.duration_seconds is not None:
            elapsed = time.monotonic() - wall_start
            if elapsed >= config.duration_seconds:
                logger.info("Duration limit reached (%.1f s). Stopping.", elapsed)
                break

        if config.dry_run:
            print(json.dumps(reading, default=str))
        else:
            try:
                status, body = _send_reading(
                    config.api_base_url,
                    reading,
                    config.api_key,
                    config.request_timeout_seconds,
                )
                duplicate = body.get("duplicate", False) if isinstance(body, dict) else False
                logger.info(
                    "step=%d status=%d duplicate=%s event_id=%s",
                    step,
                    status,
                    duplicate,
                    reading.get("source_event_id"),
                )
                if status not in (200, 201):
                    logger.warning("Unexpected status %d: %s", status, body)
            except OSError as exc:
                logger.error("Network error at step %d: %s", step, exc)

        step += 1

        # Sleep for real-time pacing
        if not config.dry_run:
            time.sleep(config.interval_seconds)

    logger.info("Simulator finished after %d readings.", step)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m simulator.runner",
        description=(
            "MechTech motor simulator — generates simulated telemetry readings.\n"
            "DISCLAIMER: Simulated data only. Not real-world fault evidence."
        ),
    )
    parser.add_argument("--equipment-id", required=True, help="Target equipment UUID.")
    parser.add_argument(
        "--scenario",
        default="normal",
        choices=["normal", "overheating", "bearing_wear", "combined", "noisy_sensor"],
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--interval-seconds", type=float, default=5.0)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--duration-seconds", type=float, default=None)
    parser.add_argument("--api-base-url", default="http://localhost:8000/api/v1")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print readings; do not POST.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser


if __name__ == "__main__":
    args = _build_cli_parser().parse_args()
    logging.basicConfig(level=args.log_level, format="%(asctime)s %(levelname)s %(message)s")

    cfg = SimulatorConfig(
        equipment_id=args.equipment_id,
        scenario=args.scenario,
        seed=args.seed,
        interval_seconds=args.interval_seconds,
        max_steps=args.max_steps,
        duration_seconds=args.duration_seconds,
        api_base_url=args.api_base_url,
        api_key=args.api_key,
        dry_run=args.dry_run,
    )
    run(cfg)

