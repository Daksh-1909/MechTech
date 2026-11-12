from fastapi import APIRouter

from app.modules.admin.router import router as admin_router
from app.modules.alerts.router import router as alerts_router
from app.modules.audit.router import router as audit_router
from app.modules.auth.router import router as auth_router
from app.modules.diagnostics.router import router as diagnostics_router
from app.modules.equipment.router import router as equipment_router
from app.modules.files.router import router as files_router
from app.modules.knowledge_graph.router import router as knowledge_graph_router
from app.modules.maintenance.router import router as maintenance_router
from app.modules.ml.router import router as ml_router
from app.modules.monitoring.router import router as monitoring_router
from app.modules.organizations.router import router as organizations_router
from app.modules.sensors.router import router as sensors_router
from app.modules.users.router import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(audit_router, prefix="/audit-logs", tags=["audit"])
api_router.include_router(equipment_router, prefix="/equipment", tags=["equipment"])
api_router.include_router(sensors_router, tags=["sensors"])
api_router.include_router(monitoring_router, tags=["monitoring"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(diagnostics_router, prefix="/diagnoses", tags=["diagnostics"])
api_router.include_router(ml_router, tags=["ml"])
api_router.include_router(
    knowledge_graph_router,
    prefix="/knowledge-graph",
    tags=["knowledge-graph"],
)
api_router.include_router(
    maintenance_router,
    prefix="/maintenance-records",
    tags=["maintenance"],
)
api_router.include_router(
    maintenance_router,
    prefix="/maintenance",
    tags=["maintenance"],
)
api_router.include_router(files_router, prefix="/files", tags=["files"])
