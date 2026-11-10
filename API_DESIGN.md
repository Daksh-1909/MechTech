# MechTech — API Design

**Version:** 1.0 · **Base path:** `/api/v1`

## 1. API conventions
- REST over HTTPS for public deployment; HTTP on loopback for local development.
- JSON request/response bodies.
- UUID resource identifiers.
- UTC timestamps in ISO 8601.
- Pydantic request and response schemas.
- Stable error codes; never expose stack traces.
- Explicit pagination and maximum page sizes.
- Authentication and authorization enforced server-side.

## 2. Error response
Use one consistent envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be validated.",
    "request_id": "correlation-id",
    "details": []
  }
}
```

Do not return secrets, SQL statements, filesystem paths, or internal exception text.

## 3. Endpoint inventory

| Area | Method and endpoint | Purpose |
|---|---|---|
| Auth | `POST /auth/register` | Submit registration request |
| Auth | `POST /auth/login` | Create session for active user |
| Auth | `POST /auth/logout` | Revoke current session |
| Auth | `GET /auth/me` | Current user and permissions |
| Auth | `POST /auth/password/change` | Change password |
| Admin | `GET /admin/registrations` | List pending registrations |
| Admin | `POST /admin/registrations/{id}/approve` | Approve registration |
| Admin | `POST /admin/registrations/{id}/reject` | Reject registration |
| Admin | `POST /admin/users` | Admin-created account |
| Organizations | `GET /organizations` | List accessible organizations |
| Organizations | `POST /organizations` | Create organization |
| Members | `GET /organizations/{id}/members` | List members |
| Members | `POST /organizations/{id}/members` | Add member |
| Equipment | `GET /equipment` | Filter equipment |
| Equipment | `POST /equipment` | Create equipment |
| Equipment | `GET /equipment/{id}` | Equipment detail |
| Equipment | `PATCH /equipment/{id}` | Update equipment |
| Equipment | `POST /equipment/{id}/archive` | Archive equipment |
| Components | `GET /equipment/{id}/components` | List components |
| Components | `POST /equipment/{id}/components` | Add component |
| Sensors | `GET /equipment/{id}/sensors` | List sensors |
| Sensors | `POST /equipment/{id}/sensors` | Register sensor |
| Telemetry | `POST /telemetry/readings:batch` | Ingest bounded reading batch |
| Telemetry | `GET /sensors/{id}/readings` | Query readings by time range |
| Monitoring | `GET /monitoring/rules` | List rules |
| Monitoring | `POST /monitoring/rules` | Create rule |
| Alerts | `GET /alerts` | Filter alerts |
| Alerts | `POST /alerts/{id}/acknowledge` | Acknowledge alert |
| Alerts | `POST /alerts/{id}/resolve` | Resolve alert |
| Diagnostics | `GET /diagnoses` | List diagnoses |
| Diagnostics | `GET /diagnoses/{id}` | Diagnosis with evidence |
| Diagnostics | `POST /diagnoses/{id}/review` | Record human review |
| ML | `GET /ml/models` | List model versions |
| ML | `POST /ml/models/{id}/activate` | Activate validated model |
| Knowledge | `GET /knowledge/nodes` | Search graph nodes |
| Knowledge | `GET /knowledge/nodes/{id}/neighbors` | Traverse graph |
| Maintenance | `GET /maintenance` | List maintenance records |
| Maintenance | `POST /maintenance` | Create maintenance record |
| Files | `POST /files` | Upload authorized file |
| Files | `GET /files/{id}` | Download authorized file |
| Audit | `GET /audit-logs` | Authorized audit search |
| Health | `GET /health/live` | Process liveness |
| Health | `GET /health/ready` | Dependency readiness |

## 4. Authorization matrix

| Capability | Viewer | Maintainer | Org Admin | Platform Admin |
|---|---:|---:|---:|---:|
| Read permitted equipment | Yes | Yes | Yes | Yes |
| Ingest simulator readings | No | Yes | Yes | Yes |
| Acknowledge/resolve alerts | No | Yes | Yes | Yes |
| Review diagnoses | No | Yes | Yes | Yes |
| Create maintenance records | No | Yes | Yes | Yes |
| Manage organization members | No | No | Yes | Yes |
| Approve registrations | No | No | Configurable | Yes |
| Manage platform roles | No | No | No | Yes |

Treat this as a starting policy. Define permission keys rather than scattering role-name checks through code.

## 5. Telemetry batch contract
A batch should include a bounded list of readings. Each reading contains `sensor_id`, `value`, `unit`, `recorded_at`, and an idempotency key. Reject oversized batches, unknown sensors, unauthorized organizations, incompatible units, and invalid timestamps. Return accepted, duplicate, and rejected counts with per-item errors that do not leak sensitive data.

## 6. Pagination and filtering
- Use `limit` with a conservative default and a hard maximum.
- Use cursor pagination for sensor readings and other high-volume feeds.
- Validate time windows and cap maximum query ranges.
- Allowlist sortable fields; never interpolate arbitrary sort expressions.
- Include stable ordering with a unique tie-breaker.

## 7. API security
- Apply authentication and permission dependencies to protected routes.
- Scope database access to authorized organization IDs.
- Validate ownership of every nested resource.
- Apply request-size limits and rate limits to login, registration, and ingestion.
- Protect cookie-authenticated writes against CSRF.
- Configure explicit CORS origins.
- Use idempotency keys for retryable ingestion and selected create operations.
