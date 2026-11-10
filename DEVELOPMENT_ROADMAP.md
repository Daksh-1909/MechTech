# MechTech — Development Roadmap

**Approach:** build one tested vertical slice at a time. Keep the project local-first and avoid premature infrastructure.

## Phase 0 — Repository and engineering foundation
**Deliverables**
- Repository structure and contribution conventions.
- Python and Node version pinning.
- Environment configuration and `.env.example`.
- Ruff, ESLint, formatter, and test runners.
- PostgreSQL local environment and Alembic baseline.
- CI workflow for linting and tests.

**Exit criteria:** a clean checkout can install dependencies, start the database, run migrations, and execute tests.

## Phase 1 — Identity, organizations, and authorization
**Deliverables**
- Users, roles, permissions, sessions.
- Public registration with pending approval.
- Admin-created accounts.
- Organizations and memberships.
- Audit events for security-sensitive actions.

**Exit criteria:** pending users are blocked; admins can approve users; cross-organization access tests pass.

## Phase 2 — Equipment and sensor foundations
**Deliverables**
- Equipment type registry.
- Generic equipment and motor-specific specifications.
- Components and sensors.
- Validation and lifecycle operations.

**Exit criteria:** authorized users can create an electric motor, components, and sensors with ownership checks.

## Phase 3 — Telemetry simulator and ingestion
**Deliverables**
- Python motor simulator with deterministic scenarios.
- Bounded batch ingestion endpoint.
- Unit and timestamp validation.
- Idempotency and quality status.
- Time-range reading query.

**Exit criteria:** simulator data is stored and queried; duplicate batches do not create duplicate readings.

## Phase 4 — Monitoring and alerts
**Deliverables**
- Configurable threshold and duration rules.
- Background evaluation.
- Anomaly and alert lifecycle.
- Dashboard summaries and bounded charts.

**Exit criteria:** a known simulated fault scenario triggers a reproducible alert with evidence.

## Phase 5 — Hybrid diagnostics
**Deliverables**
- ML model registry and versioned inference contract.
- Baseline scikit-learn model and evaluation report.
- Knowledge graph schema and NetworkX service.
- Diagnostic orchestrator and evidence persistence.
- Human review workflow.

**Exit criteria:** diagnosis records show rule, ML, and graph evidence; uncertain outputs remain advisory and reviewable.

## Phase 6 — Maintenance and files
**Deliverables**
- Maintenance records and status workflow.
- Secure local file storage.
- Audit trail and retention notes.

**Exit criteria:** authorized users can link maintenance work to equipment, alerts, and diagnoses.

## Phase 7 — Frontend and 3D experience
**Deliverables**
- Feature-based React application.
- Auth and administration flows.
- Equipment, monitoring, alert, diagnosis, and maintenance screens.
- Interactive 3D motor model with component selection.
- Responsive and accessible states.

**Exit criteria:** core workflows can be completed from the UI; 3D assets are lazy-loaded and do not block dashboard use.

## Phase 8 — Hardening and optional public deployment
**Deliverables**
- End-to-end test suite.
- Performance profiling and query review.
- Backup and restore procedure.
- Security review.
- Deployment configuration, HTTPS, secrets, monitoring, and retention controls.

**Exit criteria:** documented deployment and restore procedures work; public release security checklist passes.

## Working rules
1. Do not start a later phase while the current phase's exit criteria are failing.
2. Write tests alongside each feature.
3. Keep migrations small and reviewed.
4. Do not introduce Redis, microservices, Kubernetes, or a graph database without measured justification.
5. Record model limitations and data provenance.
6. Use synthetic data until lawful, representative real data is available.
7. Do not present simulated predictions as real equipment diagnoses.
