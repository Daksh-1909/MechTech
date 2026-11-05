import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.models import SensorReading
from app.models.equipment import Equipment
from app.modules.equipment import repository as equipment_repository
from app.modules.monitoring import service as monitoring_service
from app.modules.sensors import repository
from app.modules.sensors.schemas import (
    ReadingCreateRequest,
    ReadingResponse,
    ReadingSummaryResponse,
)
from app.schemas.sensor import SensorReadingPayload

logger = logging.getLogger(__name__)


def _get_equipment(db: Session, equipment_id: str) -> Equipment:
    equipment = equipment_repository.get_equipment(db, equipment_id)
    if equipment is None:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)
    return equipment


def _get_active_equipment(db: Session, equipment_id: str) -> Equipment:
    equipment = _get_equipment(db, equipment_id)
    if equipment.is_archived:
        raise AppError(
            "Archived equipment cannot receive readings.",
            code="EQUIPMENT_ARCHIVED",
            status_code=409,
        )
    return equipment


def _reading_values(payload: ReadingCreateRequest) -> dict:
    return {
        "equipment_id": payload.equipment_id,
        "timestamp": payload.timestamp,
        "temperature_c": payload.temperature_c,
        "vibration_value": payload.vibration_value,
        "vibration_unit": payload.vibration_unit,
        "source": payload.source,
        "source_event_id": payload.source_event_id,
        "schema_version": payload.schema_version,
        "sequence_number": payload.sequence_number,
        "speed_rpm": payload.speed_rpm,
        "load_percent": payload.load_percent,
        "scenario_id": payload.scenario_id,
        "scenario_label": payload.scenario_label,
        "simulation_seed": payload.simulation_seed,
        "simulation_run_id": payload.simulation_run_id,
        "quality_status": payload.quality_status.value,
    }


def _contract_to_request(payload: SensorReadingPayload) -> ReadingCreateRequest:
    return ReadingCreateRequest(
        equipment_id=payload.equipment_id,
        timestamp=payload.timestamp,
        temperature_c=payload.temperature_c,
        vibration_value=payload.vibration_value,
        vibration_unit=payload.vibration_unit,
        source=payload.source,
        source_event_id=payload.source_event_id,
        schema_version=payload.schema_version,
        sequence_number=payload.sequence,
        speed_rpm=payload.speed_rpm,
        load_percent=payload.load_percent,
        scenario_id=payload.scenario_id,
        scenario_label=payload.scenario_label,
        simulation_seed=payload.simulation_seed,
        simulation_run_id=payload.simulation_run_id,
    )


def ingest_contract_single(
    db: Session,
    *,
    payload: SensorReadingPayload,
) -> tuple[ReadingResponse, bool]:
    return ingest_single(db, payload=_contract_to_request(payload))


def ingest_contract_batch(
    db: Session,
    *,
    payloads: list[SensorReadingPayload],
) -> tuple[list[ReadingResponse], int, int]:
    return ingest_batch(db, payloads=[_contract_to_request(payload) for payload in payloads])


def _evaluate_new_readings(db: Session, readings: list[SensorReading]) -> None:
    for reading in readings:
        try:
            monitoring_service.evaluate_reading(db, reading)
        except Exception:
            logger.exception(
                "Failed to evaluate reading %s for equipment %s",
                reading.id,
                reading.equipment_id,
            )


def ingest_single(
    db: Session,
    *,
    payload: ReadingCreateRequest,
) -> tuple[ReadingResponse, bool]:
    _get_active_equipment(db, payload.equipment_id)

    if payload.source_event_id is not None:
        existing = repository.get_by_event_id(
            db,
            equipment_id=payload.equipment_id,
            source=payload.source,
            source_event_id=payload.source_event_id,
        )
        if existing is not None:
            return ReadingResponse.model_validate(existing), True

    if payload.sequence_number is not None:
        existing = repository.get_by_sequence(
            db,
            equipment_id=payload.equipment_id,
            sequence_number=payload.sequence_number,
        )
        if existing is not None:
            return ReadingResponse.model_validate(existing), True

    reading = repository.create_reading(db, **_reading_values(payload))
    db.commit()
    db.refresh(reading)
    _evaluate_new_readings(db, [reading])
    return ReadingResponse.model_validate(reading), False


def ingest_batch(
    db: Session,
    *,
    payloads: list[ReadingCreateRequest],
) -> tuple[list[ReadingResponse], int, int]:
    created_models: list[SensorReading] = []
    created_by_key: dict[tuple[str, str, str], SensorReading] = {}
    created_by_sequence: dict[tuple[str, int], SensorReading] = {}
    results: list[tuple[SensorReading, bool]] = []
    equipment_cache: dict[str, Equipment] = {}

    for payload in payloads:
        if payload.equipment_id not in equipment_cache:
            equipment_cache[payload.equipment_id] = _get_active_equipment(
                db,
                payload.equipment_id,
            )

        key: tuple[str, str, str] | None = None
        if payload.source_event_id is not None:
            key = (payload.equipment_id, payload.source, payload.source_event_id)
            if key in created_by_key:
                results.append((created_by_key[key], True))
                continue

            existing = repository.get_by_event_id(
                db,
                equipment_id=payload.equipment_id,
                source=payload.source,
                source_event_id=payload.source_event_id,
            )
            if existing is not None:
                results.append((existing, True))
                continue

        sequence_key = (
            (payload.equipment_id, payload.sequence_number)
            if payload.sequence_number is not None
            else None
        )
        if sequence_key is not None:
            if sequence_key in created_by_sequence:
                results.append((created_by_sequence[sequence_key], True))
                continue
            existing = repository.get_by_sequence(
                db,
                equipment_id=payload.equipment_id,
                sequence_number=payload.sequence_number,
            )
            if existing is not None:
                results.append((existing, True))
                continue

        reading = repository.create_reading(db, **_reading_values(payload))
        created_models.append(reading)
        results.append((reading, False))
        if key is not None:
            created_by_key[key] = reading
        if sequence_key is not None:
            created_by_sequence[sequence_key] = reading

    db.commit()
    for reading in created_models:
        db.refresh(reading)
    _evaluate_new_readings(db, created_models)

    duplicate_count = sum(1 for _, duplicate in results if duplicate)
    return (
        [ReadingResponse.model_validate(reading) for reading, _ in results],
        len(created_models),
        duplicate_count,
    )


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_range(start: datetime | None, end: datetime | None) -> None:
    if start is not None and end is not None and start > end:
        raise AppError(
            "The start of the range must not be after its end.",
            code="INVALID_RANGE",
            status_code=400,
        )

    if start is not None and end is not None:
        maximum = timedelta(days=settings.reading_query_max_range_days)
        if end - start > maximum:
            raise AppError(
                f"The requested range exceeds {settings.reading_query_max_range_days} days.",
                code="RANGE_TOO_LARGE",
                status_code=400,
            )


def list_readings(
    db: Session,
    *,
    equipment_id: str,
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> list[ReadingResponse]:
    _get_equipment(db, equipment_id)
    start = _to_utc(start)
    end = _to_utc(end)
    _validate_range(start, end)
    readings = repository.list_readings(
        db,
        equipment_id=equipment_id,
        start=start,
        end=end,
        limit=min(limit, settings.reading_query_max_limit),
    )
    return [ReadingResponse.model_validate(reading) for reading in readings]


def get_latest_reading(db: Session, *, equipment_id: str) -> ReadingResponse:
    _get_equipment(db, equipment_id)
    reading = repository.get_latest_reading(db, equipment_id)
    if reading is None:
        raise AppError("No readings found.", code="NOT_FOUND", status_code=404)
    return ReadingResponse.model_validate(reading)


def summarize_readings(
    db: Session,
    *,
    equipment_id: str,
    start: datetime | None,
    end: datetime | None,
) -> ReadingSummaryResponse:
    _get_equipment(db, equipment_id)
    start = _to_utc(start)
    end = _to_utc(end)
    _validate_range(start, end)
    summary = repository.summarize_readings(
        db,
        equipment_id=equipment_id,
        start=start,
        end=end,
    )
    return ReadingSummaryResponse(equipment_id=equipment_id, **summary)
