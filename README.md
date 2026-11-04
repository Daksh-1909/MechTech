# MechTech

**Detect. Diagnose. Maintain.**

An intelligent equipment monitoring and fault diagnosis platform for electric
motors, combining simulated sensor data, machine learning, a realistic 3D motor
view and a repair knowledge graph.

> Zero-budget, local-first prototype. Simulated data only. Not an industrial
> safety system. See [`MechTech_Phase_1_Requirements.md`](./MechTech_Phase_1_Requirements.md).

## Status

Phase 1 requirements are complete. This repository is currently a **project
scaffold**: dependencies, tooling and folder structure are in place; feature
implementation follows the Phase 2 design.

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
uvicorn app.main:app --reload --app-dir backend
# http://127.0.0.1:8000/docs  and  /health

# Frontend (separate terminal)
npm run dev --prefix .\frontend
# http://localhost:5173

# Simulator scaffold (separate terminal)
.\.venv\Scripts\Activate.ps1
python -m simulator.simulator --scenario normal --interval 2 --seed 42
```

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
│   │   ├── api/          # routers, dependencies
│   │   ├── core/         # settings, security
│   │   ├── db/           # engine, session, Base
│   │   ├── ml/           # anomaly detection + classification
│   │   ├── graph/        # NetworkX knowledge graph
│   │   ├── models/       # SQLAlchemy models (Phase 2)
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # business logic
│   ├── alembic/          # migrations
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/   # UI components (shadcn/ui under components/ui)
│       ├── lib/          # utilities
│       └── test/         # Vitest setup
├── simulator/            # local Python sensor simulator
├── docs/                 # Phase 2 design documents
└── MechTech_Phase_1_Requirements.md
```

## Security notes

- Secrets belong in `backend/.env` (git-ignored); never commit real keys.
- Roles must be enforced by the backend, never only in the UI.
- Set a strong `SECRET_KEY` for any non-local use:
  `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- Keep ML inference local; no paid API keys are required.

## Roadmap

Phase 2 design documents (see [`docs/README.md`](./docs/README.md)) must be
reviewed before large-scale implementation. Then implement vertical slices:
auth/roles, equipment, readings/simulator ingestion, dashboard, ML, 3D view,
knowledge graph and maintenance records.
