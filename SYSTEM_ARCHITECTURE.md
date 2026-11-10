# MechTech — System Architecture

**Version:** 1.0 · **Status:** Finalized baseline

## 1. Architecture summary
Use a **modular monolith with a separate Python background worker**. React communicates with a versioned FastAPI REST API. PostgreSQL is the source of truth for structured data. A local storage adapter stores uploads and model artifacts. A diagnostic orchestrator coordinates rules, ML, and knowledge-graph reasoning.

## 2. Approved decisions
- Audience: academic demonstration and future real users.
- Registration: public requests require administrator approval; administrators can create accounts.
- Equipment: electric motors first, extensible to other types.
- Diagnostics: rules + ML + knowledge graph.
- Deployment: local-first, optional public deployment later.

Use one application and one set of domain workflows for both audiences. Provide a seeded demonstration workspace and restricted demonstration role rather than a separate demo implementation.

## 3. Architecture principles
1. Modular monolith before microservices.
2. Explicit API, application, domain, and infrastructure boundaries.
3. PostgreSQL as authoritative structured storage.
4. Local operation without paid services.
5. Server-side authentication and authorization.
6. Organization-level data isolation.
7. Explainable diagnostic evidence and human review.
8. Versioned ML models and diagnostic policy.
9. Bounded and observable background processing.
10. Add infrastructure only when requirements and measurements justify it.

## 4. Logical architecture

```text
Browser
  |
React + TypeScript
  |
FastAPI /api/v1
  |
  +-- Auth and organizations
  +-- Equipment and components
  +-- Sensors and telemetry ingestion
  +-- Monitoring and alerts
  +-- Diagnostic orchestrator
  |     +-- Rule engine
  |     +-- ML inference service
  |     +-- Knowledge graph service
  +-- Maintenance and files
  |
PostgreSQL <---- Python background worker
  |                       ^
  +-- application data    |
  +-- graph records       |
  +-- job queue -----------+

Python motor simulator --> Telemetry ingestion API
Local storage adapter ----> uploads and ML artifacts
```

## 5. Backend layers
- **API:** HTTP handling, Pydantic validation, authentication, authorization, response serialization.
- **Application:** use cases, workflow coordination, transaction boundaries, job scheduling.
- **Domain:** business rules, equipment concepts, monitoring policies, diagnostic decisions, maintenance invariants.
- **Infrastructure:** repositories, PostgreSQL, file storage, model loading, jobs, logging.

Routes must not contain complex business logic. Domain logic must be testable without FastAPI.

## 6. Module boundaries
`auth`, `users`, `organizations`, `equipment`, `components`, `sensors`, `telemetry`, `monitoring`, `alerts`, `diagnostics`, `rules`, `ml`, `knowledge_graph`, `maintenance`, `files`, `audit`, `jobs`, `health`.

Modules expose stable application interfaces and do not import one another's private internals.

## 7. Equipment extensibility
Keep generic equipment fields separate from type-specific specifications. Generic fields include organization, name, asset tag, manufacturer, model, installation date, status, and equipment type. Motor-specific specifications include rated power, voltage, current, speed, phase, frequency, and motor type.

Use an `equipment_types` registry and versioned type-specific specification schema. Do not fill the generic equipment table with columns for every future machine type. Validate type-specific data at the application boundary.

## 8. Hybrid diagnostics

### Rule engine
Evaluates thresholds, duration windows, and operating conditions. A threshold breach is evidence of abnormal operation, not proof of a specific fault.

### ML engine
Provides a stable inference interface. Persist model identifier/version, feature schema, output, confidence/probability where meaningful, and evaluation provenance. Do not describe uncalibrated scores as guaranteed failure probabilities.

### Knowledge graph
Represent components, symptoms, faults, causes, inspections, and repairs as typed nodes and edges. Persist graph data in PostgreSQL and use NetworkX for initial traversal.

### Diagnostic orchestrator
1. Receives validated monitoring context.
2. Evaluates applicable rules.
3. Requests ML inference when suitable.
4. Retrieves relevant graph evidence.
5. Applies explicit, versioned combination logic.
6. Stores diagnosis and supporting evidence.
7. Schedules human review or alerts as appropriate.

Suggested states: `normal`, `attention_required`, `possible_fault`, `insufficient_data`, `under_review`, `confirmed_by_reviewer`, `dismissed`. An ML result alone cannot confirm a fault.

## 9. Telemetry pipeline
Initially, the simulator sends bounded HTTP batches. The API validates authorization, sensor identity, units, timestamps, payload size, and idempotency, persists readings, then schedules processing. Keep the internal processing interface transport-independent so MQTT or hardware gateways can be added later.

Store `recorded_at` (source event time) separately from `received_at` (server receipt time). Distinguish invalid data from unusual but valid observations.

## 10. Background processing
Use a PostgreSQL-backed job table and a separate Python worker initially. Safely claim jobs with transaction/locking, make handlers idempotent where possible, use bounded retries/backoff, record failures, and provide inspection/retry controls. Use an outbox pattern where a committed write must reliably enqueue downstream work. Do not add Redis/Celery until measured need.

## 11. Authentication and authorization
Use Argon2id and opaque cryptographically random server-side sessions. Store only a hash of the session token; send the token in an HttpOnly cookie. Use Secure in HTTPS, appropriate SameSite, expiry, revocation, and CSRF protection for cookie-authenticated state changes.

Authorization combines role permissions with resource ownership. Every organization-owned query and mutation must be scoped to an organization the user can access. Frontend route guards are not security controls.

Public registrations start as pending. Admin-created accounts use an audited workflow. Public users cannot grant themselves privileged roles.

## 12. Storage
Store file metadata and ownership in PostgreSQL and file bytes on local disk initially. Use server-generated storage keys, size/type validation, safe path handling, and authorization on download. Keep user uploads separate from trusted model artifacts. Define a storage interface for future object storage.

## 13. API conventions
- Prefix: `/api/v1`.
- Use plural resource names and UUID identifiers.
- Use UTC timestamps in ISO 8601 format.
- Validate request and response contracts with Pydantic.
- Return consistent error objects with stable machine-readable codes.
- Enforce authentication, permission, and tenant checks on the backend.
- Use bounded pagination; use cursor pagination for high-volume telemetry.
- Never expose stack traces, secrets, or filesystem paths.

## 14. Frontend architecture
Organize by feature: auth, dashboard, equipment, monitoring, alerts, diagnostics, knowledge graph, maintenance, administration, settings. Use TanStack Query for server state, Zustand only for suitable client state, React Hook Form/Zod for forms, and lazy-loaded routes. Bound chart queries and lazy-load 3D assets. The 3D motor view is an inspection aid, not evidence of physical inspection.

## 15. Technology baseline
- Frontend: React, Vite, TypeScript, Tailwind CSS, shadcn/ui.
- Data/forms: TanStack Query, Zustand, React Hook Form, Zod.
- Charts/3D: Recharts or ECharts, React Three Fiber, Drei.
- Backend: Python, FastAPI, Uvicorn, Pydantic v2.
- Data: PostgreSQL, SQLAlchemy, Alembic.
- ML/graph: NumPy, Pandas, SciPy, scikit-learn, Joblib, NetworkX.
- Security: Argon2id and opaque server-side sessions.
- Tests: Pytest, Vitest, React Testing Library, Playwright.

## 16. Local and public deployment
Local development ports: Vite `5173`, API `8000`, PostgreSQL `5432`; worker runs separately. Docker Compose is optional. Public deployment uses the same architecture with environment-specific configuration. Before public release configure HTTPS, secure cookies, explicit CORS, secret management, backups, network restrictions, safe migrations, monitoring, and privacy/retention controls.

## 17. Performance and observability
Index measured query patterns, avoid ORM N+1 queries, batch telemetry, use bounded time-series queries and cursor pagination, aggregate chart data, lazy-load 3D, and monitor slow queries, queue depth, job failures, diagnosis duration, and inference time. Consider partitioning or TimescaleDB only when volume justifies it. Use structured logs with request/job correlation IDs; keep audit records separate.

## 18. Testing
Use Pytest for backend services, permissions, ingestion, rules, ML contracts, graph reasoning, orchestration, jobs, and files. Run integration tests against PostgreSQL. Use Vitest/React Testing Library for UI and Playwright for registration approval, login, equipment creation, ingestion, anomaly detection, diagnosis review, and maintenance. ML evaluation must use separate train/validation/test data and prevent leakage.

## 19. Suggested repository layout

```text
mechtech/
  frontend/src/
    app/ components/ features/ hooks/ lib/ services/ stores/ types/
  backend/
    app/
      api/v1/ core/ domain/ application/ infrastructure/
      modules/ worker/
    migrations/
    tests/
  simulator/
    motor/ scenarios/ tests/
  storage/
    uploads/ models/
  docs/
    requirements/ architecture/ database/ api/ security/ testing/
  scripts/
  .env.example
  .gitignore
  README.md
  PROJECT_REQUIREMENTS.md
```

Create directories when their modules are implemented; avoid empty scaffolding for every future feature.

## 20. Final recommendation
Build a local-first, organization-aware modular monolith with a separate worker and explainable hybrid diagnostic engine. PostgreSQL is the source of truth; FastAPI owns backend workflows; React owns presentation; diagnostic evidence is persisted and reviewed by a human.
