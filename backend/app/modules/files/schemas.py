from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field


class StoredFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    uploaded_by: uuid.UUID
    maintenance_record_id: uuid.UUID | None = None
    original_filename: str
    media_type: str
    size_bytes: int
    checksum: str
    purpose: str
    created_at: datetime

