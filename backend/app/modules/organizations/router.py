from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
)
from app.modules.organizations import service
from app.modules.organizations.schemas import (
    AddMemberRequest,
    OrganizationCreateRequest,
    OrganizationMemberResponse,
    OrganizationResponse,
)

router = APIRouter()


@router.get("", response_model=list[OrganizationResponse])
def list_organizations(
    db: DbSession,
    actor: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[OrganizationResponse]:
    orgs = service.list_organizations(db, actor=actor, limit=limit, offset=offset)
    return [OrganizationResponse.model_validate(org) for org in orgs]


@router.post("", response_model=OrganizationResponse, status_code=201)
def create_organization(
    payload: OrganizationCreateRequest,
    db: DbSession,
    actor: CurrentUser,
    _: CsrfProtected,
) -> OrganizationResponse:
    org = service.create_organization(db, actor=actor, name=payload.name, slug=payload.slug)
    return OrganizationResponse.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: uuid.UUID,
    db: DbSession,
    actor: CurrentUser,
) -> OrganizationResponse:
    org = service.get_organization(db, actor=actor, org_id=org_id)
    return OrganizationResponse.model_validate(org)


@router.get("/{org_id}/members", response_model=list[OrganizationMemberResponse])
def list_members(
    org_id: uuid.UUID,
    db: DbSession,
    actor: CurrentUser,
) -> list[OrganizationMemberResponse]:
    return service.list_members(db, actor=actor, org_id=org_id)


@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=201)
def add_member(
    org_id: uuid.UUID,
    payload: AddMemberRequest,
    db: DbSession,
    actor: CurrentUser,
    _: CsrfProtected,
) -> OrganizationMemberResponse:
    member = service.add_member(
        db,
        actor=actor,
        org_id=org_id,
        user_id=payload.user_id,
        role_key=payload.role_key,
    )
    return OrganizationMemberResponse(
        id=member.id,
        user_id=member.user_id,
        display_name=member.user.display_name,
        email=member.user.email,
        membership_status=member.membership_status,
        joined_at=member.joined_at,
        role=payload.role_key,
    )

