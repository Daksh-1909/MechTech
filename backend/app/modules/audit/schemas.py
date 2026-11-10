from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    timestamp: datetime
    request_id: str | None = None
    details: dict[str, Any] | None = None

    # Backward compatibility
    @property
    def metadata_json(self) -> dict[str, Any] | None:
        return self.details
