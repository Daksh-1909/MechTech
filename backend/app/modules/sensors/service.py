from datetime import datetime
from typing import Any
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.permissions import Permission, has_permission
from app.models import Sensor, SensorReading, User
from app.models.enums import ReadingQuality
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.equipment import repository as eq_repo
from app.modules.equipment import service as eq_service
from app.modules.sensors import repository
from app.modules.sensors import reading_repository as reading_repo
from app.modules.sensors.schemas import (
    ReadingCreateRequest,
    ReadingResponse,
    ReadingSummaryResponse,
    TelemetryBatchRequest,
    TelemetryBatchResponse,
    TelemetryItemError,
)
from app.schemas.sensor import SensorReadingPayload


def _is_platform_admin(user: User) -> bool:
    return any(
        a.role and a.role.key in {"platform_admin", "admin"}
        for a in getattr(user, "assigned_roles", [])
    )


def create_sensor(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str,
    sensor_key: str,
    measurement_type: str,
    unit: str,
    component_id: uuid.UUID | str | None = None,
    status: str = "active",
    configuration: dict[str, Any] | None = None,
) -> Sensor:
    equipment = eq_service.get_equipment(db, actor, equipment_id)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_UPDATE, organization_id=equipment.organization_id):
        raise AppError("Permission denied to register sensors on this equipment.", code="FORBIDDEN", status_code=403)

    cid: uuid.UUID | None = None
    if component_id:
        cid = component_id if isinstance(component_id, uuid.UUID) else uuid.UUID(str(component_id))
        comp = eq_repo.get_component_by_id(db, cid)
        if not comp or comp.equipment_id != equipment.id:
            raise AppError("Referenced component must belong to the same equipment.", code="INVALID_COMPONENT", status_code=400)

    existing = repository.get_sensor_by_key(db, equipment_id=equipment.id, sensor_key=sensor_key)
    if existing:
        raise AppError(f"Sensor key '{sensor_key}' already exists for this equipment.", code="SENSOR_KEY_IN_USE", status_code=409)

    sensor = repository.create_sensor(
        db,
        organization_id=equipment.organization_id,
        equipment_id=equipment.id,
        component_id=cid,
        sensor_key=sensor_key,
        measurement_type=measurement_type,
        unit=unit,
        status=status,
        configuration=configuration,
    )

    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_UPDATED,
        resource_type="sensor",
        resource_id=sensor.id,
        actor_user_id=actor.id,
        organization_id=equipment.organization_id,
        metadata={"sensor_key": sensor.sensor_key, "equipment_id": str(equipment.id), "type": measurement_type},
    )
    db.commit()
    db.refresh(sensor)
    return sensor


def get_sensor(db: Session, actor: User, sensor_id: uuid.UUID | str) -> Sensor:
    sensor = repository.get_sensor_by_id(db, sensor_id)
    if not sensor:
        raise AppError("Sensor not found.", code="NOT_FOUND", status_code=404)

    if not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if not any(m.organization_id == sensor.organization_id for m in memberships):
            raise AppError("Access denied to this sensor.", code="FORBIDDEN", status_code=403)

    return sensor


def list_sensors(
    db: Session,
    *,
    actor: User,
    equipment_id: uuid.UUID | str | None = None,
    organization_id: uuid.UUID | str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Sensor]:
    org_id = None
    if organization_id:
        org_id = eq_service.resolve_organization_for_actor(actor, organization_id)
    elif not _is_platform_admin(actor):
        memberships = getattr(actor, "memberships", [])
        if memberships:
            org_id = memberships[0].organization_id

    eid = None
    if equipment_id:
        eq = eq_service.get_equipment(db, actor, equipment_id)
        eid = eq.id

    return repository.list_sensors(
        db,
        equipment_id=eid,
        organization_id=org_id,
        limit=limit,
        offset=offset,
    )


def update_sensor(
    db: Session,
    *,
    actor: User,
    sensor_id: uuid.UUID | str,
    changes: dict[str, Any],
) -> Sensor:
    sensor = get_sensor(db, actor, sensor_id)

    if not _is_platform_admin(actor) and not has_permission(actor, Permission.EQUIPMENT_UPDATE, organization_id=sensor.organization_id):
        raise AppError("Permission denied to update this sensor.", code="FORBIDDEN", status_code=403)

    if "component_id" in changes and changes["component_id"]:
        cid = changes["component_id"] if isinstance(changes["component_id"], uuid.UUID) else uuid.UUID(str(changes["component_id"]))
        comp = eq_repo.get_component_by_id(db, cid)
        if not comp or comp.equipment_id != sensor.equipment_id:
            raise AppError("Referenced component must belong to the same equipment.", code="INVALID_COMPONENT", status_code=400)

    updated = repository.update_sensor(db, sensor_id=sensor.id, changes=changes)
    if not updated:
        raise AppError("Sensor not found.", code="NOT_FOUND", status_code=404)

    audit_service.record_event(
        db,
        action=AuditAction.EQUIPMENT_UPDATED,
        resource_type="sensor",
        resource_id=updated.id,
        actor_user_id=actor.id,
        organization_id=sensor.organization_id,
        metadata={"changes": list(changes.keys())},
    )
    db.commit()
    db.refresh(updated)
    return updated


# ---------------------------------------------------------------------------
# Internal helpers — shared by all ingestion paths
# ---------------------------------------------------------------------------


def _resolve_equipment_and_check_access(
    db: Session,
    equipment_id: uuid.UUID | str,
) -> Any:
    """Return the Equipment ORM object; raise 404 if missing."""
    from app.modules.equipment import repository as _eq_repo

    eq = _eq_repo.get_equipment_by_id(db, equipment_id)
    if not eq:
        raise AppError("Equipment not found.", code="NOT_FOUND", status_code=404)
    return eq


def _build_reading(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    organization_id: uuid.UUID,
    timestamp: datetime,
    temperature_c: float | None,
    vibration_value: float | None,
    vibration_unit: str,
    value: float | None,
    unit: str | None,
    source: str,
    source_event_id: str | None,
    schema_version: str,
    sequence_number: int | None,
    speed_rpm: float | None,
    load_percent: float | None,
    scenario_id: str | None,
    scenario_label: str | None,
    simulation_seed: int | None,
    simulation_run_id: str | None,
    sensor_id: uuid.UUID | None = None,
) -> tuple[ReadingResponse, bool]:
    """Persist a reading with idempotency guard.

    Returns ``(ReadingResponse, is_duplicate)``.  Duplicate detection is based
    on the ``(equipment_id, source, source_event_id)`` unique constraint; a
    missing or None ``source_event_id`` always creates a new row.
    """
    # Fast-path duplicate check before the INSERT
    if source_event_id:
        existing = reading_repo.get_reading_by_event_id(
            db,
            equipment_id=equipment_id,
            source=source,
            source_event_id=source_event_id,
        )
        if existing:
            return ReadingResponse.from_model(existing), True

    try:
        reading = reading_repo.create_reading(
            db,
            organization_id=organization_id,
            equipment_id=equipment_id,
            sensor_id=sensor_id,
            timestamp=timestamp,
            temperature_c=temperature_c,
            vibration_value=vibration_value,
            vibration_unit=vibration_unit,
            value=value,
            unit=unit,
            source=source,
            source_event_id=source_event_id,
            schema_version=schema_version,
            sequence_number=sequence_number,
            speed_rpm=speed_rpm,
            load_percent=load_percent,
            scenario_id=scenario_id,
            scenario_label=scenario_label,
            simulation_seed=simulation_seed,
            simulation_run_id=simulation_run_id,
            quality_status=ReadingQuality.VALID.value,
        )
        db.commit()
        db.refresh(reading)
        return ReadingResponse.from_model(reading), False
    except IntegrityError:
        db.rollback()
        # Race condition: another request inserted the same event_id — fetch it
        if source_event_id:
            existing = reading_repo.get_reading_by_event_id(
                db,
                equipment_id=equipment_id,
                source=source,
                source_event_id=source_event_id,
            )
            if existing:
                return ReadingResponse.from_model(existing), True
        raise AppError(
            "Could not persist reading due to a database conflict.",
            code="CONFLICT",
            status_code=409,
        )


# ---------------------------------------------------------------------------
# Public ingestion API — called by the router
# ---------------------------------------------------------------------------


def ingest_single(
    db: Session,
    *,
    payload: ReadingCreateRequest,
) -> tuple[ReadingResponse, bool]:
    """Ingest a single reading from the internal ReadingCreateRequest schema."""
    eq_id = payload.equipment_id if isinstance(payload.equipment_id, uuid.UUID) else uuid.UUID(str(payload.equipment_id))
    eq = _resolve_equipment_and_check_access(db, eq_id)

    sid: uuid.UUID | None = None
    if payload.sensor_id:
        sid = payload.sensor_id if isinstance(payload.sensor_id, uuid.UUID) else uuid.UUID(str(payload.sensor_id))

    return _build_reading(
        db,
        equipment_id=eq.id,
        organization_id=eq.organization_id,
        timestamp=payload.timestamp,
        temperature_c=payload.temperature_c,
        vibration_value=payload.vibration_value,
        vibration_unit=payload.vibration_unit,
        value=payload.value,
        unit=payload.unit,
        source=payload.source,
        source_event_id=payload.source_event_id,
        schema_version=payload.schema_version,
        sequence_number=payload.sequence_number,
        speed_rpm=payload.speed_rpm,
        load_percent=payload.load_percent,
        scenario_id=payload.scenario_id,
        scenario_label=payload.scenario_label,
        simulation_seed=payload.simulation_seed,
        simulation_run_id=payload.simulation_run_id,
        sensor_id=sid,
    )


def ingest_batch(
    db: Session,
    *,
    payloads: list[ReadingCreateRequest],
) -> tuple[list[ReadingResponse], int, int]:
    """Ingest a batch of readings.

    Returns ``(readings_list, created_count, duplicate_count)``.
    Each reading is processed atomically; a duplicate does not abort the batch.
    """
    results: list[ReadingResponse] = []
    created = 0
    duplicates = 0
    for payload in payloads:
        response, is_dup = ingest_single(db, payload=payload)
        results.append(response)
        if is_dup:
            duplicates += 1
        else:
            created += 1
    return results, created, duplicates


def ingest_contract_single(
    db: Session,
    *,
    payload: SensorReadingPayload,
) -> tuple[ReadingResponse, bool]:
    """Ingest a single reading from the versioned Phase 3 contract schema."""
    eq_id = uuid.UUID(str(payload.equipment_id))
    eq = _resolve_equipment_and_check_access(db, eq_id)

    return _build_reading(
        db,
        equipment_id=eq.id,
        organization_id=eq.organization_id,
        timestamp=payload.timestamp,
        temperature_c=payload.temperature_c,
        vibration_value=payload.vibration_value,
        vibration_unit=payload.vibration_unit,
        value=None,
        unit=None,
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


def ingest_contract_batch(
    db: Session,
    *,
    payloads: list[SensorReadingPayload],
) -> tuple[list[ReadingResponse], int, int]:
    """Ingest a batch from the Phase 3 contract schema."""
    results: list[ReadingResponse] = []
    created = 0
    duplicates = 0
    for payload in payloads:
        response, is_dup = ingest_contract_single(db, payload=payload)
        results.append(response)
        if is_dup:
            duplicates += 1
        else:
            created += 1
    return results, created, duplicates


# ---------------------------------------------------------------------------
# Query helpers — called by the router for history / summary endpoints
# ---------------------------------------------------------------------------


def list_readings(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    before_id: uuid.UUID | None = None,
) -> list[ReadingResponse]:
    readings = reading_repo.list_readings(
        db,
        equipment_id=equipment_id,
        start=start,
        end=end,
        limit=limit,
        before_id=before_id,
    )
    return [ReadingResponse.from_model(r) for r in readings]


def get_latest_reading(
    db: Session,
    *,
    equipment_id: uuid.UUID,
) -> ReadingResponse:
    reading = reading_repo.get_latest_reading(db, equipment_id=equipment_id)
    if not reading:
        raise AppError(
            "No readings found for this equipment.",
            code="NOT_FOUND",
            status_code=404,
        )
    return ReadingResponse.from_model(reading)


def summarize_readings(
    db: Session,
    *,
    equipment_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
) -> ReadingSummaryResponse:
    stats = reading_repo.summarize_readings(db, equipment_id=equipment_id, start=start, end=end)
    return ReadingSummaryResponse(
        equipment_id=equipment_id,
        from_timestamp=start,
        to_timestamp=end,
        count=stats["count"],
        temperature_min=stats["temperature_min"],
        temperature_max=stats["temperature_max"],
        temperature_avg=stats["temperature_avg"],
        vibration_min=stats["vibration_min"],
        vibration_max=stats["vibration_max"],
        vibration_avg=stats["vibration_avg"],
    )


# ---------------------------------------------------------------------------
# Telemetry Batch & Sensor Queries (API_DESIGN.md Section 3 & 5)
# ---------------------------------------------------------------------------


def ingest_telemetry_batch(
    db: Session,
    *,
    payload: TelemetryBatchRequest,
    actor: User | None = None,
) -> TelemetryBatchResponse:
    accepted = 0
    duplicates = 0
    rejected = 0
    errors: list[TelemetryItemError] = []
    readings: list[ReadingResponse] = []

    sensor_cache: dict[uuid.UUID, Sensor | None] = {}

    for idx, item in enumerate(payload.readings):
        sid = item.sensor_id
        if sid not in sensor_cache:
            sensor_cache[sid] = repository.get_sensor_by_id(db, sid)

        sensor = sensor_cache[sid]
        if not sensor:
            errors.append(
                TelemetryItemError(
                    index=idx,
                    sensor_id=sid,
                    error_code="SENSOR_NOT_FOUND",
                    message="Referenced sensor does not exist.",
                )
            )
            rejected += 1
            continue

        if actor and not _is_platform_admin(actor):
            memberships = getattr(actor, "memberships", [])
            if not any(m.organization_id == sensor.organization_id for m in memberships):
                errors.append(
                    TelemetryItemError(
                        index=idx,
                        sensor_id=sid,
                        error_code="UNAUTHORIZED_ORGANIZATION",
                        message="Sensor belongs to an unauthorized organization.",
                    )
                )
                rejected += 1
                continue

        # Unit compatibility check
        expected_unit = sensor.unit.strip().lower()
        provided_unit = item.unit.strip().lower()
        if expected_unit != provided_unit:
            vibration_aliases = {
                "mm/s": "mm_s",
                "mm_s_rms": "mm_s",
                "mm_s": "mm_s",
            }
            exp_norm = vibration_aliases.get(expected_unit, expected_unit)
            prov_norm = vibration_aliases.get(provided_unit, provided_unit)
            if exp_norm != prov_norm:
                errors.append(
                    TelemetryItemError(
                        index=idx,
                        sensor_id=sid,
                        error_code="INCOMPATIBLE_UNIT",
                        message=f"Unit '{item.unit}' is incompatible with sensor unit '{sensor.unit}'.",
                    )
                )
                rejected += 1
                continue

        # Check idempotency
        if item.idempotency_key:
            existing = reading_repo.get_reading_by_sensor_event_id(
                db,
                sensor_id=sensor.id,
                source_event_id=item.idempotency_key,
            )
            if existing:
                duplicates += 1
                readings.append(ReadingResponse.from_model(existing))
                continue

        temp_c = item.value if sensor.measurement_type == "temperature" else None
        vib_val = item.value if sensor.measurement_type == "vibration" else None
        vib_unit = item.unit if sensor.measurement_type == "vibration" else "simulated_index"

        try:
            reading = reading_repo.create_reading(
                db,
                organization_id=sensor.organization_id,
                equipment_id=sensor.equipment_id,
                sensor_id=sensor.id,
                timestamp=item.recorded_at,
                temperature_c=temp_c,
                vibration_value=vib_val,
                vibration_unit=vib_unit,
                value=item.value,
                unit=item.unit,
                source="telemetry",
                source_event_id=item.idempotency_key,
                schema_version="1.0",
                sequence_number=None,
                speed_rpm=None,
                load_percent=None,
                scenario_id=None,
                scenario_label=None,
                simulation_seed=None,
                simulation_run_id=None,
                quality_status=item.quality_status.value,
                metadata_json=item.metadata,
            )
            db.commit()
            db.refresh(reading)
            accepted += 1
            readings.append(ReadingResponse.from_model(reading))
        except IntegrityError:
            db.rollback()
            if item.idempotency_key:
                existing = reading_repo.get_reading_by_sensor_event_id(
                    db,
                    sensor_id=sensor.id,
                    source_event_id=item.idempotency_key,
                )
                if existing:
                    duplicates += 1
                    readings.append(ReadingResponse.from_model(existing))
                    continue
            errors.append(
                TelemetryItemError(
                    index=idx,
                    sensor_id=sid,
                    error_code="CONFLICT",
                    message="Database constraint violation while inserting reading.",
                )
            )
            rejected += 1

    return TelemetryBatchResponse(
        accepted=accepted,
        duplicates=duplicates,
        rejected=rejected,
        errors=errors,
        readings=readings,
    )


def list_readings_by_sensor(
    db: Session,
    *,
    actor: User,
    sensor_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    before_id: uuid.UUID | None = None,
) -> list[ReadingResponse]:
    sensor = get_sensor(db, actor, sensor_id)
    readings = reading_repo.list_readings_by_sensor(
        db,
        sensor_id=sensor.id,
        start=start,
        end=end,
        limit=limit,
        before_id=before_id,
    )
    return [ReadingResponse.from_model(r) for r in readings]
