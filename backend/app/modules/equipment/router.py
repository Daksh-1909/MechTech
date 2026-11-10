from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.equipment import repository as repo
from app.modules.equipment import service
from app.modules.equipment.schemas import (
    ComponentCreateRequest,
    ComponentResponse,
    ComponentUpdateRequest,
    EquipmentAssignmentRequest,
    EquipmentAssignmentResponse,
    EquipmentCreateRequest,
    EquipmentResponse,
    EquipmentTypeResponse,
    EquipmentUpdateRequest,
)
from app.modules.sensors import service as sensor_service
from app.modules.sensors.schemas import SensorCreateRequest, SensorResponse

router = APIRouter()

EquipmentManager = Annotated[User, Depends(require_permission(Permission.EQUIPMENT_CREATE))]


@router.get("/types", response_model=list[EquipmentTypeResponse])
def list_equipment_types(db: DbSession, user: CurrentUser) -> list[EquipmentTypeResponse]:
    types = repo.list_equipment_types(db)
    return [EquipmentTypeResponse.model_validate(t) for t in types]


@router.get("", response_model=list[EquipmentResponse])
def list_equipment(
    db: DbSession,
    user: CurrentUser,
    organization_id: uuid.UUID | None = None,
    include_archived: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EquipmentResponse]:
    equipment = service.list_equipment(
        db,
        actor=user,
        organization_id=organization_id,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )
    return [service.build_equipment_response(item) for item in equipment]


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
    return service.build_equipment_response(equipment)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
def get_equipment(equipment_id: uuid.UUID, db: DbSession, user: CurrentUser) -> EquipmentResponse:
    equipment = service.get_equipment(db, user, equipment_id)
    return service.build_equipment_response(equipment)


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
def update_equipment(
    equipment_id: uuid.UUID,
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
    return service.build_equipment_response(equipment)


@router.post("/{equipment_id}/archive", response_model=EquipmentResponse)
def archive_equipment_post(
    equipment_id: uuid.UUID,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> EquipmentResponse:
    equipment = service.archive_equipment(db, actor=manager, equipment_id=equipment_id)
    return service.build_equipment_response(equipment)


@router.delete("/{equipment_id}", status_code=204)
def archive_equipment(
    equipment_id: uuid.UUID,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> Response:
    service.archive_equipment(db, actor=manager, equipment_id=equipment_id)
    return Response(status_code=204)


# Components sub-resource
@router.get("/{equipment_id}/components", response_model=list[ComponentResponse])
def list_components(
    equipment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> list[ComponentResponse]:
    components = service.list_components(db, actor=user, equipment_id=equipment_id)
    return [ComponentResponse.model_validate(item) for item in components]


@router.post(
    "/{equipment_id}/components",
    response_model=ComponentResponse,
    status_code=201,
)
def create_component(
    equipment_id: uuid.UUID,
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
        component_type=payload.component_type,
        parent_component_id=payload.parent_component_id,
        manufacturer=payload.manufacturer,
        model_number=payload.model_number,
        serial_number=payload.serial_number,
        description=payload.description,
    )
    return ComponentResponse.model_validate(component)


@router.patch(
    "/{equipment_id}/components/{component_id}",
    response_model=ComponentResponse,
)
def update_component(
    equipment_id: uuid.UUID,
    component_id: uuid.UUID,
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


# Sensors sub-resource on equipment
@router.get("/{equipment_id}/sensors", response_model=list[SensorResponse])
def list_equipment_sensors(
    equipment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> list[SensorResponse]:
    sensors = sensor_service.list_sensors(db, actor=user, equipment_id=equipment_id)
    return [SensorResponse.model_validate(s) for s in sensors]


@router.post("/{equipment_id}/sensors", response_model=SensorResponse, status_code=201)
def register_equipment_sensor(
    equipment_id: uuid.UUID,
    payload: SensorCreateRequest,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> SensorResponse:
    sensor = sensor_service.create_sensor(
        db,
        actor=manager,
        equipment_id=equipment_id,
        sensor_key=payload.sensor_key,
        measurement_type=payload.measurement_type,
        unit=payload.unit,
        component_id=payload.component_id,
        status=payload.status,
        configuration=payload.configuration,
    )
    return SensorResponse.model_validate(sensor)


# Equipment assignments sub-resource
@router.post("/{equipment_id}/assignments", response_model=EquipmentAssignmentResponse, status_code=201)
def assign_equipment_user(
    equipment_id: uuid.UUID,
    payload: EquipmentAssignmentRequest,
    db: DbSession,
    manager: EquipmentManager,
    _: CsrfProtected,
) -> EquipmentAssignmentResponse:
    assignment = service.assign_equipment(
        db,
        actor=manager,
        equipment_id=equipment_id,
        user_id=payload.user_id,
        assignment_type=payload.assignment_type,
    )
    return EquipmentAssignmentResponse.model_validate(assignment)


@router.get("/{equipment_id}/assignments", response_model=list[EquipmentAssignmentResponse])
def list_equipment_assignments(
    equipment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> list[EquipmentAssignmentResponse]:
    # verifies access through get_equipment
    service.get_equipment(db, user, equipment_id)
    assignments = repo.list_assignments(db, equipment_id)
    return [EquipmentAssignmentResponse.model_validate(a) for a in assignments]
