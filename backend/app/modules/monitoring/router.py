from fastapi import APIRouter

from app.api.deps import DbSession
from app.modules.auth.dependencies import CurrentUser
from app.modules.monitoring import service
from app.modules.monitoring.schemas import EquipmentStatusResponse

router = APIRouter()


@router.get("/monitoring/overview", response_model=list[EquipmentStatusResponse])
def overview(db: DbSession, user: CurrentUser) -> list[EquipmentStatusResponse]:
    return service.get_overview(db)


@router.get("/equipment/{equipment_id}/status", response_model=EquipmentStatusResponse)
def equipment_status(
    equipment_id: str,
    db: DbSession,
    user: CurrentUser,
) -> EquipmentStatusResponse:
    return service.get_equipment_status(db, equipment_id)
