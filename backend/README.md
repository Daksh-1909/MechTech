# MechTech Backend

FastAPI backend scaffold for MechTech.

## Local setup

```powershell
# From the repository root
.\.venv\Scripts\Activate.ps1
pip install -e ".\backend[dev]"
Copy-Item backend\.env.example backend\.env

# Run the API
uvicorn app.main:app --reload --app-dir backend
```

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

## Tests and lint

```powershell
pytest backend
ruff check backend
```
