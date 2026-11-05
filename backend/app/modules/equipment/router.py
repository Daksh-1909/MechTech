from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.equipment import service
from app.modules.equipment.schemas import (
    ComponentCreateRequest,
    ComponentResponse,
    ComponentUpdateRequest,
    EquipmentCreateRequest,
    EquipmentResponse,
    EquipmentUpdateRequest,
)

router = APIRouter()

EquipmentManager = Annotated[User, Depends(require_permission(Permission.EQUIPMENT_MANAGE))]


@router.get("", response_model=list[EquipmentResponse])
def list_equipment(
    db: DbSession,
    user: CurrentUser,
    include_archived: bool = False,
) -> list[EquipmentResponse]:
    equipment = service.list_equipment(db, include_archived=include_archived)
    return [EquipmentResponse.model_validate(item) for item in equipment]


@router.post("", response_model=EquipmentResponse, status_code=201)
def create_equipment(
    payload: EquipmentCreateRequest,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> EquipmentResponse:
    equipment = service.create_equipment(
        db,
        actor=manager,
        values=payload.model_dump(),
    )
    return EquipmentResponse.model_validate(equipment)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(equipment_id: str, db: DbSession, user: CurrentUser) -> EquipmentResponse:
    return EquipmentResponse.model_validate(service.get_equipment(db, equipment_id))


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: str,
    payload: EquipmentUpdateRequest,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> EquipmentResponse:
    equipment = service.update_equipment(
        db,
        actor=manager,
        equipment_id=equipment_id,
        changes=payload.model_dump(exclude_unset=True),
    )
    return EquipmentResponse.model_validate(equipment)


@router.delete("/{equipment_id}", status_code=204)
def archive_equipment(
    equipment_id: str,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> Response:
    service.archive_equipment(db, actor=manager, equipment_id=equipment_id)
    return Response(status_code=204)


@router.get("/{equipment_id}/components", response_model=list[ComponentResponse])
def list_components(
    equipment_id: str,
    db: DbSession,
    user: CurrentUser,
) -> list[ComponentResponse]:
    components = service.list_components(db, equipment_id=equipment_id)
    return [ComponentResponse.model_validate(item) for item in components]


@router.post(
    "/{equipment_id}/components",
    response_model=ComponentResponse,
    status_code=201,
)
def create_component(
    equipment_id: str,
    payload: ComponentCreateRequest,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> ComponentResponse:
    component = service.create_component(
        db,
        actor=manager,
        equipment_id=equipment_id,
        component_key=payload.component_key,
        name=payload.name,
        description=payload.description,
    )
    return ComponentResponse.model_validate(component)


@router.patch(
    "/{equipment_id}/components/{component_id}",
    response_model=ComponentResponse,
)
def update_component(
    equipment_id: str,
    component_id: int,
    payload: ComponentUpdateRequest,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> ComponentResponse:
    component = service.update_component(
        db,
        actor=manager,
        equipment_id=equipment_id,
        component_id=component_id,
        changes=payload.model_dump(exclude_unset=True),
    )
    return ComponentResponse.model_validate(component)
