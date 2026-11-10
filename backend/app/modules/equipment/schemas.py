from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EquipmentTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    name: str
    schema_version: str
    is_enabled: bool


class EquipmentTypeCreateRequest(BaseModel):
    key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=150)
    schema_version: str = Field(default="1.0", max_length=20)


class EquipmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    organization_id: uuid.UUID | None = None
    equipment_type_key: str = Field(default="electric_motor")
    asset_tag: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=200)
    model_number: str | None = Field(default=None, max_length=200)
    serial_number: str | None = Field(default=None, max_length=200)
    location_label: str | None = Field(default=None, max_length=200)
    installation_date: datetime | None = None
    status: str = Field(default="operational")
    specification: dict[str, Any] | None = None

    # Legacy field alias
    category: str | None = None
    location: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Equipment name must not be blank.")
        return stripped


class EquipmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    asset_tag: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=200)
    model_number: str | None = Field(default=None, max_length=200)
    serial_number: str | None = Field(default=None, max_length=200)
    location_label: str | None = Field(default=None, max_length=200)
    status: str | None = None
    specification: dict[str, Any] | None = None

    # Legacy field alias
    location: str | None = None
    description: str | None = None


class ComponentCreateRequest(BaseModel):
    component_key: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=200)
    component_type: str = Field(default="component", max_length=100)
    parent_component_id: uuid.UUID | None = None
    manufacturer: str | None = Field(default=None, max_length=200)
    model_number: str | None = Field(default=None, max_length=200)
    serial_number: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Component name must not be blank.")
        return stripped


class ComponentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    component_type: str | None = None
    parent_component_id: uuid.UUID | None = None
    status: str | None = None
    description: str | None = Field(default=None, max_length=2000)


class ComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    equipment_id: uuid.UUID
    parent_component_id: uuid.UUID | None = None
    component_key: str
    component_type: str
    name: str
    manufacturer: str | None = None
    model_number: str | None = None
    status: str
    description: str | None = None
    created_at: datetime


class EquipmentAssignmentRequest(BaseModel):
    user_id: uuid.UUID
    assignment_type: str = Field(default="primary_maintainer", max_length=50)


class EquipmentAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    equipment_id: uuid.UUID
    user_id: uuid.UUID
    assignment_type: str
    assigned_by: uuid.UUID
    assigned_at: datetime
    ended_at: datetime | None = None


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    equipment_type_id: uuid.UUID
    equipment_type_key: str = "electric_motor"
    asset_tag: str | None = None
    name: str
    manufacturer: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    location_label: str | None = None
    installation_date: datetime | None = None
    status: str
    specification: dict[str, Any] | None = None
    components_count: int = 0
    sensors_count: int = 0
    created_at: datetime
    updated_at: datetime

    # Backward compatibility
    @property
    def category(self) -> str:
        return self.equipment_type_key

    @property
    def location(self) -> str | None:
        return self.location_label
