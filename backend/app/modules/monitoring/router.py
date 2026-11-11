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
from app.modules.monitoring import service
from app.modules.monitoring.schemas import (
    EquipmentStatusResponse,
    MonitoringRuleCreateRequest,
    MonitoringRuleResponse,
    MonitoringRuleUpdateRequest,
)

router = APIRouter()

RuleManager = Annotated[User, Depends(require_permission(Permission.MONITORING_RULES_MANAGE))]


@router.get("/monitoring/rules", response_model=list[MonitoringRuleResponse], tags=["monitoring"])
def list_rules(
    db: DbSession,
    user: CurrentUser,
    organization_id: uuid.UUID | None = None,
    equipment_type_id: uuid.UUID | None = None,
    measurement_type: str | None = None,
    is_enabled: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[MonitoringRuleResponse]:
    return service.list_rules(
        db,
        actor=user,
        organization_id=organization_id,
        equipment_type_id=equipment_type_id,
        measurement_type=measurement_type,
        is_enabled=is_enabled,
        limit=limit,
        offset=offset,
    )


@router.post("/monitoring/rules", response_model=MonitoringRuleResponse, status_code=201, tags=["monitoring"])
def create_rule(
    payload: MonitoringRuleCreateRequest,
    db: DbSession,
    manager: RuleManager,
    _: CsrfProtected,
) -> MonitoringRuleResponse:
    return service.create_rule(db, actor=manager, payload=payload)


@router.get("/monitoring/rules/{rule_id}", response_model=MonitoringRuleResponse, tags=["monitoring"])
def get_rule(
    rule_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> MonitoringRuleResponse:
    return service.get_rule(db, actor=user, rule_id=rule_id)


@router.patch("/monitoring/rules/{rule_id}", response_model=MonitoringRuleResponse, tags=["monitoring"])
def update_rule(
    rule_id: uuid.UUID,
    payload: MonitoringRuleUpdateRequest,
    db: DbSession,
    manager: RuleManager,
    _: CsrfProtected,
) -> MonitoringRuleResponse:
    return service.update_rule(db, actor=manager, rule_id=rule_id, payload=payload)


@router.delete("/monitoring/rules/{rule_id}", status_code=204, tags=["monitoring"])
def delete_rule(
    rule_id: uuid.UUID,
    db: DbSession,
    manager: RuleManager,
    _: CsrfProtected,
) -> Response:
    service.delete_rule(db, actor=manager, rule_id=rule_id)
    return Response(status_code=204)


@router.get("/monitoring/overview", response_model=list[EquipmentStatusResponse], tags=["monitoring"])
def overview(
    db: DbSession,
    user: CurrentUser,
    organization_id: uuid.UUID | None = None,
) -> list[EquipmentStatusResponse]:
    return service.get_overview(db, actor=user, organization_id=organization_id)


@router.get("/equipment/{equipment_id}/status", response_model=EquipmentStatusResponse, tags=["monitoring"])
def equipment_status(
    equipment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> EquipmentStatusResponse:
    return service.get_equipment_status(db, actor=user, equipment_id=equipment_id)
