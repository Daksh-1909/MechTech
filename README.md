# MechTech

**Detect. Diagnose. Maintain.**

An intelligent equipment monitoring and fault diagnosis platform for electric
motors, combining simulated sensor data, machine learning, a realistic 3D motor
view and a repair knowledge graph.

> Zero-budget, local-first prototype. Simulated data only. Not an industrial
> safety system. See [`MechTech_Phase_1_Requirements.md`](./MechTech_Phase_1_Requirements.md).

## Status

Phase 1 requirements and all Phase 2 backend milestones **2.1-2.10** are
implemented: typed settings, request-ID middleware, standard error envelopes,
structured JSON logging with redaction, health/version endpoints, SQLite with
foreign keys and WAL, Alembic migrations, isolated test fixtures, Argon2id
password hashing, server-side sessions, HttpOnly cookies, CSRF protection,
backend-enforced role permissions, admin-only user administration, redacted
audit events, equipment/components, idempotent sensor ingestion, monitoring,
anomalies and alerts, local ML training/evaluation and safe inference, a
persisted knowledge graph, maintenance records, a security test suite, benchmark
tooling, and tested SQLite backup/restore. Frontend, 3D and deployment remain
out of scope for Phase 2.

## Tech stack

| Area | Technologies |
| --- | --- |
| Frontend | React, Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Zustand, React Hook Form, Zod, Recharts, React Three Fiber, Drei, React Flow, Framer Motion |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic, WebSockets |
| Data / ML | SQLite, NumPy, Pandas, SciPy, scikit-learn, joblib, NetworkX |
| Quality | pytest, Vitest, Playwright, Ruff, oxlint, Prettier |

## Prerequisites (Windows 11)

- Node.js 20+ and npm
- Python 3.13 (installed at `%LOCALAPPDATA%\Programs\Python\Python313`)
- Git

Python was added to the user PATH during setup. Open a new terminal for it to
take effect.

## Setup

```powershell
# From the repository root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".\backend[dev]"

# Frontend dependencies
npm install --prefix .\frontend

# Local backend configuration
Copy-Item backend\.env.example backend\.env
```

## Run

```powershell
# Backend API + docs
.\.venv\Scripts\Activate.ps1
Set-Location backend
alembic upgrade head
python scripts\bootstrap_admin.py   # first run only
Set-Location ..
uvicorn app.main:app --reload --app-dir backend
# http://127.0.0.1:8000/docs
# http://127.0.0.1:8000/health/live  and  /health/ready  and  /version

# Frontend (separate terminal)
npm run dev --prefix .\frontend
# http://localhost:5173

# Simulator (separate terminal)
.\.venv\Scripts\Activate.ps1
$env:SIMULATOR_API_KEY = "local-simulator-key"   # match backend .env
python -m simulator.simulator --scenario normal --interval 2 --seed 42

# Reference knowledge and model tooling (from backend/)
Set-Location backend
python scripts\seed_knowledge_graph.py --admin-email admin@example.com
python scripts\train_anomaly_model.py --register --admin-email admin@example.com
python scripts\evaluate_model.py --model-id 1 --update-registry
python scripts\backup_restore.py backup
python scripts\backup_restore.py verify --path ..\data\backups\mechtech-<timestamp>.db
Set-Location ..
```

Start the simulator only after registering the equipment with `POST /api/v1/equipment`.
For benchmark measurements, keep the API running and run
`python scripts\benchmark.py --email admin@example.com` from `backend/`.

## Tests, lint and format

```powershell
.\.venv\Scripts\Activate.ps1
pytest backend
ruff check backend

npm test --prefix .\frontend
npm run lint --prefix .\frontend
npm run build --prefix .\frontend
```

## Project structure

```text
MechTech/
├── backend/
│   ├── app/
│   │   ├── api/          # API router and dependencies
│   │   ├── core/         # settings, security, logging, paths
│   │   ├── db/           # engine, session, Base, types
│   │   ├── ml/           # features, datasets, evaluation, safe loading
│   │   ├── models/       # SQLAlchemy models and enums
│   │   └── modules/      # auth, users, equipment, sensors, monitoring,
│   │                     # alerts, ML, knowledge graph, maintenance, audit
│   ├── alembic/          # migrations
│   ├── scripts/          # bootstrap, training, seeding, benchmark, backup
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/   # UI components (shadcn/ui under components/ui)
│       ├── lib/          # utilities
│       └── test/         # Vitest setup
├── simulator/            # local Python sensor simulator
├── data/                 # local runtime data (db, models, datasets, logs)
├── docs/                 # Phase 2 design documents
└── MechTech_Phase_1_Requirements.md
```

## Security notes

- Secrets belong in `backend/.env` (git-ignored); never commit real keys.
- Roles must be enforced by the backend, never only in the UI. RBAC policy
  lives in `app/core/permissions.py` and is checked in dependencies and
  services; self role escalation is rejected.
- Sessions are opaque server-side tokens stored as SHA-256 hashes; the raw
  token lives only in an `HttpOnly` cookie. CSRF tokens are required for
  state-changing requests.
- Audit metadata is bounded and redacted; passwords and raw session tokens are
  never stored in audit records.
- Set `SESSION_COOKIE_SECURE=true` whenever the API is served over HTTPS.
- Keep ML inference local; no paid API keys are required.
- Model artifacts are loaded only from `DATA_ROOT/models`; do not treat model
  files as executable uploads.
- Run `scriptsackup_restore.py verify` after a backup and restore into a
  separate database before relying on it.

## Roadmap

Phase 2 backend milestones (see
[`MechTech_Phase_2_Backend_Architecture.md`](./MechTech_Phase_2_Backend_Architecture.md)):

- [x] 2.1 Backend foundation
- [x] 2.2 Database foundation
- [x] 2.3 Users and authentication (opaque sessions)
- [x] 2.4 RBAC and audit
- [x] 2.5 Equipment and components
- [x] 2.6 Sensor ingestion and querying
- [x] 2.7 Monitoring, anomalies and alerts
- [x] 2.8 ML integration
- [x] 2.9 Knowledge graph and maintenance
- [x] 2.10 Hardening and performance baseline

Frontend, 3D visualization and deployment follow in later phases.
