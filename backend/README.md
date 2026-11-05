# MechTech Backend

FastAPI backend for the local MechTech prototype. Phase 2 milestones 2.1-2.10
are implemented: typed settings, SQLite/Alembic, authentication and RBAC, audit
logging, equipment and readings, monitoring/alerts, ML training and inference,
a persisted knowledge graph, maintenance records, security tests, benchmark
tooling and tested backup/restore.

> All sensor values and ML outputs are prototype data. Thresholds are not
> industrial safety limits and predictions are not confirmed diagnoses.

## Local setup

```powershell
# From the repository root
.\.venv\Scripts\Activate.ps1
pip install -e ".\backend[dev]"
Copy-Item backend\.env.example backend\.env

# Run the API
uvicorn app.main:app --reload --app-dir backend
```

- OpenAPI docs: http://127.0.0.1:8000/docs
- API contract: [`../docs/api-contract.md`](../docs/api-contract.md)
- Liveness: http://127.0.0.1:8000/health/live
- Readiness (checks SQLite): http://127.0.0.1:8000/health/ready
- Version: http://127.0.0.1:8000/version

Every response includes an `X-Request-ID` header and errors use this envelope:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Not Found",
    "request_id": "4f2c1d9e8a7b4c3d9f0e1a2b3c4d5e6f"
  }
}
```

## Database and migrations

SQLite is the local source of truth. The default file is
`data/db/mechtech.db` at the repository root, configurable through `DATA_ROOT`
and `DATABASE_URL`. Relative SQLite paths resolve against the repository root.

```powershell
Set-Location backend
alembic upgrade head
alembic current
Set-Location ..
```

Every connection enables `PRAGMA foreign_keys=ON`, WAL journal mode and a busy
timeout. Migrations use batch mode for SQLite. Tests apply migrations to a
temporary database; they never touch the developer database.

## Authentication and authorization

Passwords use Argon2id. Sessions are random 256-bit opaque tokens; only a
SHA-256 hash is stored. The raw token lives in the HttpOnly
`mechtech_session` cookie and a per-session CSRF token is exposed in the
readable `mechtech_csrf` cookie. Unsafe methods must send `X-CSRF-Token` and a
trusted `Origin`.

Endpoints under `/api/v1/auth`:

- `POST /login`, `POST /logout`, `GET /me`
- `GET /sessions`, `DELETE /sessions/{id}`
- `POST /change-password`

Create the first administrator interactively:

```powershell
Set-Location backend
python scripts\bootstrap_admin.py
```

Roles are `admin`, `technician` and `operator`; permissions live in
`app/core/permissions.py` and are enforced in backend dependencies and service
policy checks. Admin-only user management is under `/api/v1/users`; audit
records are read-only under `/api/v1/audit-logs`.

## Domain API

| Area | Main endpoints |
| --- | --- |
| Equipment | `GET/POST /equipment`, `GET/PATCH/DELETE /equipment/{id}`, component create/list/update |
| Readings | `POST /readings`, `POST /readings/batch`, historical/latest/summary reads |
| Monitoring | `GET /monitoring/overview`, `GET /equipment/{id}/status` |
| Alerts | `GET /alerts`, `GET /alerts/{id}`, `PATCH /alerts/{id}/status` |
| ML | `POST /equipment/{id}/analysis`, `GET /predictions`, `GET /models` |
| Knowledge graph | graph view, node detail, bounded neighbors, admin node/edge writes |
| Maintenance | list/create/detail/update maintenance records |

Sensor ingestion accepts a session with `READINGS_INGEST` or a valid
`X-Device-Key` matching `SIMULATOR_API_KEY`. Duplicate `source_event_id` values
per equipment/source are idempotent. Archived equipment remains queryable but
cannot receive readings/components or new maintenance records.

Anomaly evaluation is rule-based and configurable. Controlled threshold
breaches create anomaly events and deduplicated alerts. Alert acknowledgement,
resolution and dismissal are admin/technician actions.

## Phase 3 sensor-to-ML pipeline

Generate a deterministic labeled CSV dataset from the repository root:

```powershell
python -m simulator.simulator --export-csv data/exports/phase3.csv --samples-per-scenario 120 --seed 42
```

Create equipment, then run the simulator with `SIMULATOR_API_KEY` configured
to send readings through the authenticated ingestion endpoint. Batch requests
are bounded by `READINGS_BATCH_MAX` (default 100). Reading source metadata and
raw values remain separate from immutable feature-window snapshots.

Train and evaluate models from the repository root (artifacts and reports are
written under `DATA_ROOT/models`):

```powershell
python backend/scripts/train_statistical_baseline.py --samples-per-scenario 120 --seed 42 --output data/exports/baseline-report.json
python backend/scripts/train_isolation_forest.py --train-runs 6 --evaluation-runs 2 --samples-per-scenario 120 --seed 42
python backend/scripts/train_random_forest.py --runs 8 --test-runs 2 --samples-per-scenario 120 --seed 42
```

The baseline trainer writes a versioned profile/report; the two ML trainers
write joblib artifacts and JSON evaluation reports. Add `--register` and
`--admin-email admin@example.com` to register an artifact inactive, then have
an administrator activate its registry entry with `POST
/api/v1/models/{model_id}/activate`. Do not activate a model based only on a
synthetic metric; review the report and data provenance first.

An administrator can optionally queue bounded local training through
`POST /api/v1/train` and poll `GET /api/v1/training-jobs/{job_id}`. The API
requires an admin session and CSRF token. Only one queued/running job is
allowed; the worker is a single process-local thread. Training jobs never
activate the resulting model automatically. See the [Phase 3 completion
report](../docs/phase-3-completion.md) for verification and limitations.

## Legacy Phase 2 ML workflow

The Phase 2 anomaly trainer remains available for backward compatibility:

```powershell
Set-Location backend
python scripts\train_anomaly_model.py --register --admin-email admin@example.com
python scripts\evaluate_model.py --model-id 1 --update-registry
```

The trainer writes a joblib artifact under `DATA_ROOT/models` plus a JSON
metrics report. `--register` activates the model in the registry and records an
audit event. Evaluation writes a separate report and can update registry
metrics. Runtime analysis requires at least two recent readings and an active
classification model; missing or unsafe artifacts return a safe error and are
never silently replaced.

Model artifacts are loaded only from `DATA_ROOT/models`; arbitrary filesystem
paths and uploaded executable artifacts are rejected.

## Knowledge graph and maintenance

`GET /knowledge-graph` returns bounded nodes and edges from SQLite. Neighbors
are traversed through NetworkX with `depth` limited to 1-3 and bounded result
counts. Admin writes are audited. Rebuild the reference graph idempotently:

```powershell
Set-Location backend
python scripts\seed_knowledge_graph.py --admin-email admin@example.com
```

Maintenance records link equipment and optional same-equipment alerts. Admins
can edit any record; technicians can edit their own.

## Simulator

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
$env:SIMULATOR_API_KEY = "local-simulator-key"
python -m simulator.simulator --scenario normal --interval 2 --seed 42
```

Supported scenarios include normal, increased vibration, overheating, combined
abnormality, sensor disconnection, noisy sensor and return to normal. Use
`--batch-size` to exercise batch ingestion. The simulator never bypasses
authentication: it uses `X-Device-Key` or an authenticated ingestion session.

## Logging, backup and performance

Application logs are structured JSON and include `request_id`, level, logger
and message. Sensitive key/value patterns are redacted. Audit metadata has
separate size limits and redaction.

```powershell
Set-Location backend
python scripts\backup_restore.py backup
python scripts\backup_restore.py verify --path ..\data\backups\<file>.db
python scripts\backup_restore.py restore --backup ..\data\backups\<file>.db --force
```

SQLite's backup API is used instead of copying a live database file. Restore
validates integrity before replacing a target, and the test suite covers a
backup/restore round trip. Stop the API before restoring the active database.

With the API running:

```powershell
python scripts\benchmark.py --email admin@example.com
```

The benchmark measures p50/p95/p99 response times for health and authenticated
read endpoints, writes a JSON report under `DATA_ROOT/exports`, and records the
Python/platform/database environment. See
[`../docs/performance-baseline.md`](../docs/performance-baseline.md) for the
current recorded baseline and limitations.

## Configuration

Typed settings live in `app/core/config.py` and are read from `backend/.env`.
Key values:

- `APP_ENV`, `LOG_LEVEL`, `API_V1_PREFIX`, `DATA_ROOT`, `DATABASE_URL`
- `SESSION_COOKIE_NAME`, `CSRF_COOKIE_NAME`, `CSRF_HEADER_NAME`
- `SESSION_TTL_HOURS`, `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_SAMESITE`
- `SIMULATOR_API_KEY`, `DEVICE_API_KEY_HEADER`
- reading bounds, batch/query limits, stale-data threshold and anomaly thresholds
- `FEATURE_WINDOW_SIZE`, `ANALYSIS_WINDOW_MAX`

Invalid values fail at startup. Writable data lives under `data/` (`db`,
`models`, `datasets`, `exports`, `backups`, `logs`) and is excluded from Git.

## Tests and lint

```powershell
.\.venv\Scripts\Activate.ps1
pytest backend -q
ruff check backend simulator
ruff format --check backend simulator
```

Tests use a temporary SQLite database and temporary `DATA_ROOT`, cover
authorization, ingestion/idempotency, alerts, ML safety, graph traversal,
maintenance ownership, CSRF, secrets exposure, logging redaction, benchmark
math, training/evaluation and backup/restore.
