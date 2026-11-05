"""Measure local API response-time percentiles for a documented baseline."""

import argparse
import getpass
import json
import math
import os
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings
from app.core.paths import ensure_data_directories


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark local MechTech API endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--email",
        help="Administrator or technician email for authenticated reads.",
    )
    parser.add_argument("--equipment-id", default="motor-001")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output", help="Optional JSON report path.")
    return parser


def percentile(values: list[float], percent: float) -> float:
    if not values:
        raise ValueError("values must not be empty.")
    ordered = sorted(values)
    rank = max(1, math.ceil((percent / 100.0) * len(ordered)))
    return ordered[min(rank - 1, len(ordered) - 1)]


def summarize(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "p50_ms": round(percentile(values, 50), 3),
        "p95_ms": round(percentile(values, 95), 3),
        "p99_ms": round(percentile(values, 99), 3),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
        "mean_ms": round(sum(values) / len(values), 3),
    }


def measure(
    client: httpx.Client,
    url: str,
    *,
    iterations: int,
    warmup: int,
) -> dict[str, Any]:
    statuses: set[int] = set()
    for _ in range(warmup):
        response = client.get(url)
        statuses.add(response.status_code)

    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        response = client.get(url)
        samples.append((time.perf_counter() - started) * 1000.0)
        statuses.add(response.status_code)

    return {
        "url": url,
        "status_codes": sorted(statuses),
        **summarize(samples),
    }


def _login(client: httpx.Client, base_url: str, email: str) -> None:
    password = os.environ.get("MECHTECH_BENCH_PASSWORD") or getpass.getpass("Password: ")
    response = client.post(
        f"{base_url}{settings.api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code != 200:
        raise RuntimeError(f"Benchmark login failed with HTTP {response.status_code}.")


def main() -> int:
    args = build_parser().parse_args()
    ensure_data_directories()
    base_url = args.base_url.rstrip("/")
    prefix = settings.api_v1_prefix

    endpoints = [f"{base_url}/health/live"]
    with httpx.Client(timeout=args.timeout, follow_redirects=True) as client:
        if args.email:
            try:
                _login(client, base_url, args.email)
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            endpoints.extend(
                [
                    f"{base_url}{prefix}/equipment",
                    f"{base_url}{prefix}/monitoring/overview",
                    f"{base_url}{prefix}/equipment/{args.equipment_id}",
                    f"{base_url}{prefix}/equipment/{args.equipment_id}/status",
                    (f"{base_url}{prefix}/equipment/{args.equipment_id}/readings?limit=100"),
                    f"{base_url}{prefix}/knowledge-graph",
                ]
            )

        results = []
        for url in endpoints:
            try:
                results.append(
                    measure(
                        client,
                        url,
                        iterations=args.iterations,
                        warmup=args.warmup,
                    )
                )
            except httpx.HTTPError as exc:
                print(f"Benchmark failed for {url}: {exc}", file=sys.stderr)
                return 1

    report = {
        "measured_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "iterations": args.iterations,
        "warmup": args.warmup,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "database_url": settings.database_url,
            "data_root": str(settings.data_root),
            "authenticated": bool(args.email),
        },
        "results": results,
        "note": (
            "Local prototype measurements only. Percentiles depend on machine load, "
            "SQLite state and endpoint data volume."
        ),
    }

    output = (
        Path(args.output)
        if args.output
        else settings.data_root
        / "exports"
        / f"benchmark-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(f"{'endpoint':<70} {'status':>7} {'p50':>9} {'p95':>9} {'p99':>9}")
    for result in results:
        print(
            f"{result['url']:<70} "
            f"{','.join(str(code) for code in result['status_codes']):>7} "
            f"{result['p50_ms']:>8.2f}ms "
            f"{result['p95_ms']:>8.2f}ms "
            f"{result['p99_ms']:>8.2f}ms"
        )
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
