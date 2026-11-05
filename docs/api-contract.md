# MechTech API contract

Phase 2 backend contract for the local prototype. This document is descriptive;
FastAPI's generated OpenAPI schema at `/openapi.json` and `/docs` is the
authoritative interactive reference.

## Conventions

- Base URL: `http://127.0.0.1:8000`
- Version prefix: `/api/v1`
- Content type: `application/json`
- Timestamps: ISO 8601 UTC. Naive timestamps are treated as UTC.
- Vibration: normalized prototype indicator. Supported units are
  `simulated_index`, `mm_s_rms`, `mm_s`, `g` and `arbitrary_unit`.
- Idempotency: readings are unique per `(equipment_id, source, source_event_id)`
  when `source_event_id` is provided.
- Pagination: list endpoints use bounded `limit` and `offset` query parameters.
- Safety: simulated data, prototype thresholds and predictions are not
  industrial safety limits or confirmed diagnoses.

## Authentication and CSRF

Human users authenticate with `POST /api/v1/auth/login`, which sets:

- `mechtech_session`: HttpOnly opaque session cookie.
- `mechtech_csrf`: readable per-session CSRF token.

Unsafe methods must send the CSRF value in `X-CSRF-Token`; the request may also
need a trusted `Origin` from the configured CORS allowlist.

Sensor ingestion accepts either:

- A valid session for an admin or technician, or
- `X-Device-Key` matching the configured `SIMULATOR_API_KEY`.

## Roles

| Capability | Admin | Technician | Operator |
| --- | :---: | :---: | :---: |
| View equipment, readings, monitoring, alerts, predictions | Yes | Yes | Yes |
| Ingest readings | Yes | Yes | No |
| Manage equipment/components | Yes | No | No |
| Manage alerts | Yes | Yes | No |
| Create/edit maintenance records | Yes | Yes | No |
| Request ML analysis and view model metadata | Yes | Yes | No |
| Queue training jobs and activate models | Yes | No | No |
| Edit knowledge graph reference data | Yes | No | No |
| Manage users and view audit logs | Yes | No | No |

## Errors

Errors use one envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The submitted request is invalid.",
    "request_id": "4f2c1d9e8a7b4c3d9f0e1a2b3c4d5e6f",
    "details": [
      {
        "field": "temperature_c",
        "issue": "Temperature is outside the configured prototype bounds."
      }
    ]
  }
}
```

`X-Request-ID` is returned on every response and appears in the error body.
Unexpected exceptions never include tracebacks in the response.

## Phase 3 sensor and ML pipeline

`POST /api/v1/readings` accepts a validated single sensor reading;
`POST /api/v1/readings/batch` accepts up to `READINGS_BATCH_MAX` readings
(default 100). Both persist raw inputs and apply the same timestamp,
measurement, equipment and idempotency rules. The batch endpoint is intended
for simulator/device ingestion.

`POST /api/v1/equipment/{equipment_id}/analysis` stores an advisory prediction
for the latest complete feature window. Its evidence includes feature schema,
source reading IDs, the immutable feature-window snapshot, model provenance,
classification score semantics, and any active baseline/anomaly-detector
results. Read history through `GET /api/v1/predictions` or equipment-scoped
prediction/anomaly history endpoints with bounded `limit`/`offset`.

Admin-only model lifecycle endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/models` | List safe registry metadata; artifact paths are not exposed |
| POST | `/api/v1/models/{model_id}/activate` | Verify artifact checksum/schema and activate explicitly |
| POST | `/api/v1/train` | Queue one bounded synthetic training job; returns 202 |
| GET | `/api/v1/training-jobs/{job_id}` | Read job state, result, or safe error text |

Training submission requires an admin session and CSRF token. Request fields
are `model_type` (`anomaly` or `classification`), `model_name`,
`model_version`, `runs` (2–20), `test_runs` (1–5),
`samples_per_scenario` (40–1000), and `seed`. Optional classifier
`minimum_score` defaults to 0.4; optional anomaly `contamination` defaults to
0.05. Jobs are single-flight and queued in one local worker thread. They
register trained models inactive; use the activation endpoint after reviewing
the held-out report. Training-job execution is process-local and intended for
one local API process.

Feature schema `2.0` contains a count plus mean, median, standard deviation,
minimum, maximum, RMS, peak-to-peak, slope, rate of change, rolling standard
deviation, last value and delta for temperature and vibration. Missing or
incomplete windows are marked explicitly; RMS-like vibration simulation
values use `simulated_index`, not physical mm/s RMS.

## Equipment

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/v1/equipment` | Authenticated |
| POST | `/api/v1/equipment` | Admin |
| GET | `/api/v1/equipment/{equipment_id}` | Authenticated |
| PATCH | `/api/v1/equipment/{equipment_id}` | Admin |
| DELETE | `/api/v1/equipment/{equipment_id}` | Admin, archives |
| GET | `/api/v1/equipment/{equipment_id}/components` | Authenticated |
| POST | `/api/v1/equipment/{equipment_id}/components` | Admin |
| PATCH | `/api/v1/equipment/{equipment_id}/components/{component_id}` | Admin |

Archive is a status change, not a hard delete. Archived equipment remains
queryable directly and keeps its component, reading, alert and maintenance
history. Archived equipment cannot receive new readings or components.

Example registration:

```json
{
  "id": "motor-001",
  "name": "Press Motor",
  "category": "electric_motor",
  "manufacturer": "Example Motors",
  "location": "Line A"
}
```

## Readings

| Method | Endpoint | Access |
| --- | --- | --- |
| POST | `/api/v1/readings` | Device key or admin/technician |
| POST | `/api/v1/readings/batch` | Device key or admin/technician |
| GET | `/api/v1/equipment/{equipment_id}/readings` | Authenticated |
| GET | `/api/v1/equipment/{equipment_id}/readings/latest` | Authenticated |
| GET | `/api/v1/equipment/{equipment_id}/readings/summary` | Authenticated |

Single-reading example:

```json
{
  "equipment_id": "motor-001",
  "timestamp": "2026-11-05T12:00:00Z",
  "temperature_c": 54.2,
  "vibration_value": 0.18,
  "vibration_unit": "simulated_index",
  "source": "simulator",
  "source_event_id": "run-42-0001",
  "quality_status": "valid"
}
```

At least one sensor channel is required. A first write returns `201`; a
replayed `source_event_id` returns `200` with `duplicate: true`.

Historical queries accept `from`, `to` and `limit`; results are ordered oldest
first. Ranges must be ordered and are bounded by `READING_QUERY_MAX_RANGE_DAYS`.
The summary endpoint returns count, min/max/average for each channel.

## Monitoring and alerts

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/v1/monitoring/overview` | Authenticated |
| GET | `/api/v1/equipment/{equipment_id}/status` | Authenticated |
| GET | `/api/v1/alerts` | Authenticated |
| GET | `/api/v1/alerts/{alert_id}` | Authenticated |
| PATCH | `/api/v1/alerts/{alert_id}/status` | Admin/technician |

Alert filters: `status`, `equipment_id`, `severity`, `limit`, `offset`.
Statuses are `open`, `acknowledged`, `resolved` and `dismissed`. Closed alerts
cannot be reopened or dismissed again.

The prototype rule engine creates anomaly events and alerts from configurable
temperature/vibration thresholds. Open alerts are deduplicated by equipment and
alert type. Returning to normal closes the open anomaly episode.

## ML

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/v1/predictions` | Authenticated |
| GET | `/api/v1/predictions/{prediction_id}` | Authenticated |
| POST | `/api/v1/equipment/{equipment_id}/analysis` | Admin/technician |
| GET | `/api/v1/models` | Admin/technician |

Analysis requires at least two recent readings and an active registered
classification model. Predictions persist the model registry id, feature schema
version, feature window, probabilities and confidence. If the active model is
missing or its trusted artifact cannot be loaded, the API returns a safe `503`
or `409` error; it never substitutes a different model silently.

Model artifacts are loaded only from `DATA_ROOT/models`; arbitrary paths are
rejected. Training happens in `backend/scripts/train_anomaly_model.py`, not in
request handlers.

## Knowledge graph

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/v1/knowledge-graph` | Authenticated |
| GET | `/api/v1/knowledge-graph/nodes/{node_id}` | Authenticated |
| GET | `/api/v1/knowledge-graph/nodes/{node_id}/neighbors` | Authenticated |
| POST | `/api/v1/knowledge-graph/nodes` | Admin |
| PATCH | `/api/v1/knowledge-graph/nodes/{node_id}` | Admin |
| POST | `/api/v1/knowledge-graph/edges` | Admin |

Graph traversal is bounded by `depth` (1-3) and `limit`. SQLite is the source of
truth; NetworkX is rebuilt from stored nodes and edges for traversal.

## Maintenance

| Method | Endpoint | Access |
| --- | --- | --- |
| GET | `/api/v1/maintenance-records` | Authenticated |
| POST | `/api/v1/maintenance-records` | Admin/technician |
| GET | `/api/v1/maintenance-records/{record_id}` | Authenticated |
| PATCH | `/api/v1/maintenance-records/{record_id}` | Admin or owning technician |

A related alert must belong to the same equipment. Technicians may edit their
own records; admins may edit any record. Archived equipment accepts no new
maintenance records.
