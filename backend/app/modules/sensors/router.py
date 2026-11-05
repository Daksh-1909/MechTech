from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.deps import DbSession
from app.core.config import settings
from app.modules.auth.dependencies import CurrentUser, IngestionAccess
from app.modules.sensors import service
from app.modules.sensors.schemas import (
    ReadingBatchRequest,
    ReadingBatchResponse,
    ReadingCreateRequest,
    ReadingIngestResponse,
    ReadingResponse,
    ReadingSummaryResponse,
)
from app.schemas.sensor import SensorReadingBatchPayload, SensorReadingPayload

router = APIRouter()


@router.post("/sensor-readings", response_model=ReadingIngestResponse)
def ingest_versioned_reading(
    payload: SensorReadingPayload,
    response: Response,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingIngestResponse:
    reading, duplicate = service.ingest_contract_single(db, payload=payload)
    response.status_code = 200 if duplicate else 201
    return ReadingIngestResponse(reading=reading, duplicate=duplicate)


@router.post("/sensor-readings/batch", response_model=ReadingBatchResponse, status_code=201)
def ingest_versioned_readings_batch(
    payload: SensorReadingBatchPayload,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingBatchResponse:
    readings, created, duplicates = service.ingest_contract_batch(db, payloads=payload.readings)
    return ReadingBatchResponse(created=created, duplicates=duplicates, readings=readings)


@router.post("/readings", response_model=ReadingIngestResponse)
def ingest_reading(
    payload: ReadingCreateRequest,
    response: Response,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingIngestResponse:
    reading, duplicate = service.ingest_single(db, payload=payload)
    response.status_code = 200 if duplicate else 201
    return ReadingIngestResponse(reading=reading, duplicate=duplicate)


@router.post("/readings/batch", response_model=ReadingBatchResponse, status_code=201)
def ingest_readings_batch(
    payload: ReadingBatchRequest,
    db: DbSession,
    _: IngestionAccess,
) -> ReadingBatchResponse:
    readings, created, duplicates = service.ingest_batch(db, payloads=payload.readings)
    return ReadingBatchResponse(created=created, duplicates=duplicates, readings=readings)


@router.get("/equipment/{equipment_id}/readings", response_model=list[ReadingResponse])
def list_readings(
    equipment_id: str,
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


@router.get("/equipment/{equipment_id}/readings/latest", response_model=ReadingResponse)
def latest_reading(equipment_id: str, db: DbSession, user: CurrentUser) -> ReadingResponse:
    return service.get_latest_reading(db, equipment_id=equipment_id)


@router.get(
    "/equipment/{equipment_id}/readings/summary",
    response_model=ReadingSummaryResponse,
)
def summarize_readings(
    equipment_id: str,
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
