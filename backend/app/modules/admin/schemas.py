from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.security import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.modules.auth.schemas import UserResponse


class RegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    display_name: str
    status: str
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by: uuid.UUID | None = None
    review_note: str | None = None


class ApproveRegistrationRequest(BaseModel):
    organization_id: uuid.UUID | None = None
    role_key: str = Field(default="viewer")
    review_note: str | None = Field(default=None, max_length=1000)


class RejectRegistrationRequest(BaseModel):
    review_note: str | None = Field(default=None, max_length=1000)


class AdminCreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    role: str = Field(default="viewer")
    organization_id: uuid.UUID | None = None

