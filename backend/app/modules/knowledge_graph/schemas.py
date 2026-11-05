from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import NodeType, RelationshipType


class NodeCreateRequest(BaseModel):
    node_type: NodeType
    stable_key: str = Field(min_length=1, max_length=150)
    label: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    attributes_json: dict[str, Any] | None = None


class NodeUpdateRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    attributes_json: dict[str, Any] | None = None


class EdgeCreateRequest(BaseModel):
    source_node_id: int
    target_node_id: int
    relationship_type: RelationshipType
    description: str | None = Field(default=None, max_length=4000)
    attributes_json: dict[str, Any] | None = None


class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    node_type: NodeType
    stable_key: str
    label: str
    description: str | None
    attributes_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class EdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_node_id: int
    target_node_id: int
    relationship_type: RelationshipType
    description: str | None
    attributes_json: dict[str, Any] | None
    created_at: datetime


class GraphResponse(BaseModel):
    nodes: list[NodeResponse]
    edges: list[EdgeResponse]
    meta: dict[str, Any]
