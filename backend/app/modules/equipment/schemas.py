from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import EquipmentStatus

_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"


class EquipmentCreateRequest(BaseModel):
    id: str | None = Field(default=None, pattern=_ID_PATTERN)
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="electric_motor", min_length=1, max_length=50)
    manufacturer: str | None = Field(default=None, max_length=200)
    model_number: str | None = Field(default=None, max_length=200)
    serial_number: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: EquipmentStatus = EquipmentStatus.ACTIVE

    @field_validator("name", "category")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value must not be blank.")
        return stripped


class EquipmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    manufacturer: str | None = Field(default=None, max_length=200)
    model_number: str | None = Field(default=None, max_length=200)
    serial_number: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: EquipmentStatus | None = None

    @field_validator("name", "category")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value must not be blank.")
        return stripped


class ComponentCreateRequest(BaseModel):
    component_key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Name must not be blank.")
        return stripped


class ComponentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: str
    component_key: str
    name: str
    description: str | None
    created_at: datetime


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    manufacturer: str | None
    model_number: str | None
    serial_number: str | None
    location: str | None
    description: str | None
    status: EquipmentStatus
    created_at: datetime
    updated_at: datetime


class EquipmentListResponse(BaseModel):
    data: list[EquipmentResponse]
    meta: dict[str, object]
