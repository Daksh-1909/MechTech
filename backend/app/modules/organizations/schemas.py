from datetime import datetime
import re
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=2, max_length=100)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        s = value.strip().lower()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", s):
            raise ValueError("Slug must contain lowercase alphanumeric characters and hyphens only.")
        return s


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: str
    created_at: datetime
    updated_at: datetime


class OrganizationMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    email: EmailStr
    membership_status: str
    joined_at: datetime
    role: str | None = None


class AddMemberRequest(BaseModel):
    user_id: uuid.UUID
    role_key: str = Field(default="viewer")

