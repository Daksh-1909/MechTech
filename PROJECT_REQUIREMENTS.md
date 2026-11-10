# MechTech — Project Requirements

**Version:** 1.0 · **Status:** Approved baseline  
**Tagline:** Detect. Diagnose. Maintain.

## 1. Product vision
MechTech is a local-first equipment-monitoring and fault-diagnosis platform. It initially focuses on electric motors and combines simulated sensor data, rule-based anomaly detection, machine-learning predictions, knowledge-graph reasoning, maintenance workflows, and realistic 3D visualization.

The product serves both academic demonstration and future real maintenance users through one shared application architecture. The initial release uses simulated data and is not a certified industrial safety system or a replacement for professional inspection.

## 2. Approved architecture decisions

| Area | Approved decision |
|---|---|
| Audience | Academic demonstration and future real users |
| Registration | Public registration subject to admin approval; admins can also create accounts |
| Equipment | Electric motors initially; architecture extensible to other equipment |
| Diagnostics | Combined rules + ML + knowledge-graph reasoning |
| Deployment | Local-first; public deployment optional later |

## 3. Goals
- Manage users, organizations, equipment, components, sensors, alerts, diagnoses, and maintenance.
- Simulate realistic motor telemetry and fault scenarios.
- Validate and persist sensor readings with explicit units and timestamps.
- Detect abnormal conditions using configurable rules.
- Support versioned ML models and traceable predictions.
- Relate symptoms, components, causes, faults, inspections, and repairs through a knowledge graph.
- Combine diagnostic evidence through a testable diagnostic orchestrator.
- Require human review before a diagnosis is marked confirmed.
- Provide an interactive 3D motor view.
- Run locally without paid services.
- Keep the equipment model extensible.

## 4. Non-goals for the initial release
- Certified industrial control or safety functionality.
- Direct control of physical motors.
- Guaranteed fault prediction or remaining-useful-life estimation.
- Mandatory cloud hosting, microservices, Kubernetes, Redis, or a separate graph database.
- Deep-learning models without suitable data and evaluation evidence.

## 5. Users and roles

| Role | Capabilities |
|---|---|
| Platform Administrator | Platform-level administration |
| Organization Administrator | Organization, membership, equipment, and settings |
| Maintainer | Monitoring, diagnosis review, and maintenance |
| Viewer | Read-only access to permitted records |
| Demonstration User | Restricted seeded demonstration workspace |

Public registration creates a pending account. An administrator approves or rejects it. Administrators can also create accounts directly. Public registration must never grant privileged roles.

## 6. Functional requirements

### FR-01 — Identity and access
Login/logout, public registration, approval/rejection, administrator-created accounts, session revocation, and server-side permission checks.

### FR-02 — Organizations
Users belong to organizations through memberships. Organization-owned records must be isolated. Seed a demonstration organization for academic use.

### FR-03 — Equipment
Create, view, update, assign, and archive equipment. Store generic equipment fields separately from type-specific specifications. Initial type: electric motor.

### FR-04 — Sensors and telemetry
Register sensors and ingest bounded batches. Store value, unit, recorded time, received time, source, and quality status. Validate sensor ownership, unit compatibility, timestamps, payload size, and duplicate submissions.

### FR-05 — Monitoring and alerts
Configure threshold/window rules, evaluate readings, create anomalies and alerts, and support acknowledge/resolve/dismiss workflows with audit history.

### FR-06 — Machine learning
Support model metadata and versions, feature schemas, predictions, and evaluation metrics. Predictions are advisory.

### FR-07 — Knowledge graph
Represent equipment, components, symptoms, faults, causes, inspections, and repairs with typed relationships. Use NetworkX initially, with graph records persisted in PostgreSQL.

### FR-08 — Diagnostics
Combine rule results, ML outputs, and graph evidence. Persist diagnostic policy version and evidence. Support human review, confirmation, and dismissal.

### FR-09 — Maintenance
Create tasks and maintenance records linked to equipment and optionally a diagnosis or alert.

### FR-10 — Files
Validate uploads, store bytes outside public source directories, and store metadata/ownership in PostgreSQL.

### FR-11 — Visualization
Show backend-derived dashboard metrics, bounded sensor charts, and interactive 3D motor visualization with component/sensor selection and diagnostic highlighting.

### FR-12 — Operations
Provide health checks, structured logs, correlation IDs, auditable events, and observable background jobs with bounded retries.

## 7. Non-functional requirements
- **Security:** Argon2id password hashing, opaque server-side sessions, CSRF protection, RBAC, object-level authorization, tenant isolation, safe uploads, secret management, HTTPS in public deployment.
- **Integrity:** Foreign keys, constraints, transactions, idempotent job handlers, tested migrations.
- **Performance:** Bounded pagination, indexed telemetry queries, batch ingestion, background processing, lazy-loaded 3D assets.
- **Maintainability:** Modular backend, explicit boundaries, Alembic migrations, automated tests, stable API schemas.
- **Usability:** Clear loading, empty, error, and permission states; explain simulated data and diagnostic uncertainty.

## 8. Technology baseline

| Area | Technology |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| UI/data | shadcn/ui, Lucide, TanStack Query, Zustand |
| Forms | React Hook Form, Zod |
| Charts/3D | Recharts or ECharts; React Three Fiber and Drei |
| Backend | Python, FastAPI, Uvicorn, Pydantic v2 |
| Persistence | PostgreSQL, SQLAlchemy, Alembic |
| Security | Argon2id, secure cookie sessions |
| ML/data | NumPy, Pandas, SciPy, scikit-learn, Joblib, SHAP where useful |
| Graph | NetworkX |
| Testing | Pytest, Vitest, React Testing Library, Playwright |
| Quality | Ruff, ESLint |
| Local services | Docker Compose optional |

## 9. First end-to-end acceptance criteria
1. An administrator creates an organization and manages members.
2. A public user registers and cannot access protected features before approval.
3. An authorized user creates an electric motor and sensors.
4. The simulator submits readings; the backend validates and stores them.
5. A configured rule detects a simulated abnormal condition and creates an alert.
6. The diagnostic workflow combines available rule, ML, and graph evidence.
7. An authorized human can review the diagnosis.
8. A maintenance record can reference equipment and diagnosis.
9. Organization isolation has automated tests.
10. The system runs locally without paid services.
11. The UI clearly labels simulated data and advisory predictions.
