# Performance baseline

Measured local prototype baseline for Phase 2, milestone 2.10. These numbers
are observations, not targets or capacity guarantees.

## Environment

| Item | Value |
| --- | --- |
| Date | 2026-11-05 |
| Operating system | Windows 11 `10.0.26300` |
| Python | 3.13.7, 64-bit |
| Database | SQLite, WAL mode, foreign keys enabled |
| Server | Uvicorn, single worker, `127.0.0.1:8765` |
| Data set | 1 equipment, 200 recent readings, empty knowledge graph |
| Load | Sequential requests: 10 warm-up + 100 measured per endpoint |
| Auth | Authenticated admin session for `/api/v1` reads |

## Results

All requests returned HTTP `200`. Times are milliseconds.

| Endpoint | p50 | p95 | p99 |
| --- | ---: | ---: | ---: |
| `GET /health/live` | 0.944 | 1.122 | 1.242 |
| `GET /api/v1/equipment` | 2.090 | 2.539 | 2.830 |
| `GET /api/v1/monitoring/overview` | 2.649 | 3.436 | 4.158 |
| `GET /api/v1/equipment/motor-001` | 1.999 | 2.523 | 2.805 |
| `GET /api/v1/equipment/motor-001/status` | 2.610 | 3.261 | 3.978 |
| `GET /api/v1/equipment/motor-001/readings?limit=100` | 3.434 | 4.088 | 4.150 |
| `GET /api/v1/knowledge-graph` | 2.337 | 2.820 | 2.927 |

Raw report: [`benchmark-baseline.json`](./benchmark-baseline.json).

## Method

The benchmark server used a fresh temporary SQLite database migrated to the
current Alembic head. An administrator, one motor and 200 normal readings were
inserted directly. The server ran without `--reload`. `scripts/benchmark.py`
logged in through the public API, then issued sequential GET requests. Warm-up
requests were excluded from percentiles.

Percentiles use nearest-rank selection over the recorded samples.

## Limitations

- Single-user, sequential traffic only; no concurrency or rate-limit testing.
- Localhost only; no network or TLS overhead.
- Tiny dataset; larger reading/alert history will change query times.
- No sensor ingestion, alert mutation, ML inference or model loading in this run.
- Machine background load and antivirus can affect results.
- The same machine and database state must be used when comparing changes.

## Reproduce

With the API running and an existing administrator:

```powershell
Set-Location backend
$env:MECHTECH_BENCH_PASSWORD = "<password>"
python scripts\benchmark.py --email admin@example.com --iterations 100 --warmup 10
```

The script writes a timestamped JSON report under `DATA_ROOT/exports`.
