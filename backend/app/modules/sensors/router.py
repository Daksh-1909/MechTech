from datetime import datetime
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import DbSession
from app.core.config import settings
from app.core.permissions import Permission
from app.models import User
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    IngestionAccess,
    require_permission,
)
from app.modules.sensors import service
from app.modules.sensors.schemas import (
    ReadingBatchRequest,
    ReadingBatchResponse,
    ReadingCreateRequest,
    ReadingIngestResponse,
    ReadingResponse,
    ReadingSummaryResponse,
    SensorResponse,
    SensorUpdateRequest,
)
from app.schemas.sensor import SensorReadingBatchPayload, SensorReadingPayload

router = APIRouter()

SensorManager = Annotated[User, Depends(require_permission(Permission.EQUIPMENT_UPDATE))]


@router.get("/sensors", response_model=list[SensorResponse], tags=["sensors"])
def list_sensors(
    db: DbSession,
    user: CurrentUser,
    equipment_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SensorResponse]:
    sensors = service.list_sensors(
        db,
        actor=user,
        equipment_id=equipment_id,
        organization_id=organization_id,
        limit=limit,
        offset=offset,
    )
    return [SensorResponse.model_validate(s) for s in sensors]


@router.get("/sensors/{sensor_id}", response_model=SensorResponse, tags=["sensors"])
def get_sensor(
    sensor_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> SensorResponse:
    sensor = service.get_sensor(db, user, sensor_id)
    return SensorResponse.model_validate(sensor)


@router.patch("/sensors/{sensor_id}", response_model=SensorResponse, tags=["sensors"])
def update_sensor(
    sensor_id: uuid.UUID,
    payload: SensorUpdateRequest,
    db: DbSession,
    manager: SensorManager,
    _: CsrfProtected,
) -> SensorResponse:
    sensor = service.update_sensor(
        db,
        actor=manager,
        sensor_id=sensor_id,
        changes=payload.model_dump(exclude_unset=True),
    )
    return SensorResponse.model_validate(sensor)


@router.post("/sensor-readings", response_model=ReadingIngestResponse, tags=["telemetry"])
def ingest_versioned_reading(
    payload: SensorReadingPayload,
    response: Response,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingIngestResponse:
    reading, duplicate = service.ingest_contract_single(db, payload=payload)
    response.status_code = 200 if duplicate else 201
    return ReadingIngestResponse(reading=reading, duplicate=duplicate)


@router.post("/sensor-readings/batch", response_model=ReadingBatchResponse, status_code=201, tags=["telemetry"])
def ingest_versioned_readings_batch(
    payload: SensorReadingBatchPayload,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingBatchResponse:
    readings, created, duplicates = service.ingest_contract_batch(db, payloads=payload.readings)
    return ReadingBatchResponse(created=created, duplicates=duplicates, readings=readings)


@router.post("/readings", response_model=ReadingIngestResponse, tags=["telemetry"])
def ingest_reading(
    payload: ReadingCreateRequest,
    response: Response,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingIngestResponse:
    reading, duplicate = service.ingest_single(db, payload=payload)
    response.status_code = 200 if duplicate else 201
    return ReadingIngestResponse(reading=reading, duplicate=duplicate)


@router.post("/readings/batch", response_model=ReadingBatchResponse, status_code=201, tags=["telemetry"])
def ingest_readings_batch(
    payload: ReadingBatchRequest,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingBatchResponse:
    readings, created, duplicates = service.ingest_batch(db, payloads=payload.readings)
    return ReadingBatchResponse(created=created, duplicates=duplicates, readings=readings)


@router.get("/equipment/{equipment_id}/readings", response_model=list[ReadingResponse], tags=["telemetry"])
def list_readings(
    equipment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=settings.reading_query_max_limit)] = 100,
) -> list[ReadingResponse]:
    return service.list_readings(
        db,
        equipment_id=equipment_id,
        start=start,
        end=end,
        limit=limit,
    )


@router.get("/equipment/{equipment_id}/readings/latest", response_model=ReadingResponse, tags=["telemetry"])
def latest_reading(equipment_id: uuid.UUID, db: DbSession, user: CurrentUser) -> ReadingResponse:
    return service.get_latest_reading(db, equipment_id=equipment_id)


@router.get(
    "/equipment/{equipment_id}/readings/summary",
    response_model=ReadingSummaryResponse,
    tags=["telemetry"],
)
def summarize_readings(
    equipment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
) -> ReadingSummaryResponse:
    return service.summarize_readings(
        db,
        equipment_id=equipment_id,
        start=start,
        end=end,
    )
