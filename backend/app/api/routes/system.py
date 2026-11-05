from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings
from app.core.exceptions import AppError

router = APIRouter(tags=["system"])


class HealthStatus(BaseModel):
    status: Literal["ok", "ready"]


class VersionInfo(BaseModel):
    name: str
    version: str
    api_prefix: str


@router.get("/health/live", response_model=HealthStatus)
def health_live() -> HealthStatus:
    return HealthStatus(status="ok")


@router.get("/health/ready", response_model=HealthStatus)
def health_ready(db: DbSession) -> HealthStatus:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise AppError(
            "The database is not ready.",
            code="NOT_READY",
            status_code=503,
        ) from exc
    return HealthStatus(status="ready")


@router.get("/version", response_model=VersionInfo)
def version() -> VersionInfo:
    return VersionInfo(
        name=settings.app_name,
        version=settings.app_version,
        api_prefix=settings.api_v1_prefix,
    )
