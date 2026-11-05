from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession
from app.core.permissions import Permission
from app.models import User
from app.models.enums import NodeType
from app.modules.auth.dependencies import (
    CsrfProtected,
    CurrentUser,
    require_permission,
)
from app.modules.knowledge_graph import service
from app.modules.knowledge_graph.schemas import (
    EdgeCreateRequest,
    EdgeResponse,
    GraphResponse,
    NodeCreateRequest,
    NodeResponse,
    NodeUpdateRequest,
)

router = APIRouter()

KnowledgeManager = Annotated[
    User,
    Depends(require_permission(Permission.KNOWLEDGE_MANAGE)),
]


@router.get("", response_model=GraphResponse)
def get_graph(
    db: DbSession,
    user: CurrentUser,
    node_type: NodeType | None = None,
    limit: Annotated[int, Query(ge=1, le=service.MAX_GRAPH_NODES)] = 200,
) -> GraphResponse:
    nodes, edges = service.get_graph(
        db,
        node_type=None if node_type is None else node_type.value,
        limit=limit,
    )
    return GraphResponse(
        nodes=[NodeResponse.model_validate(node) for node in nodes],
        edges=[EdgeResponse.model_validate(edge) for edge in edges],
        meta={"node_count": len(nodes), "edge_count": len(edges)},
    )


@router.get("/nodes/{node_id}", response_model=NodeResponse)
def get_node(node_id: int, db: DbSession, user: CurrentUser) -> NodeResponse:
    return NodeResponse.model_validate(service.get_node(db, node_id))


@router.get("/nodes/{node_id}/neighbors")
def get_neighbors(
    node_id: int,
    db: DbSession,
    user: CurrentUser,
    depth: Annotated[int, Query(ge=1, le=service.MAX_DEPTH)] = 1,
    limit: Annotated[int, Query(ge=1, le=service.MAX_NEIGHBOR_NODES)] = 50,
) -> dict[str, Any]:
    nodes, edges, total = service.get_neighbors(
        db,
        node_id=node_id,
        depth=depth,
        limit=limit,
    )
    return {
        "nodes": [NodeResponse.model_validate(node).model_dump() for node in nodes],
        "edges": [EdgeResponse.model_validate(edge).model_dump() for edge in edges],
        "meta": {"depth": depth, "total_neighbors": total},
    }


@router.post("/nodes", response_model=NodeResponse, status_code=201)
def create_node(
    payload: NodeCreateRequest,
    db: DbSession,
    manager: KnowledgeManager,
    _: CsrfProtected,
) -> NodeResponse:
    node = service.create_node(db, actor=manager, values=payload.model_dump())
    return NodeResponse.model_validate(node)


@router.patch("/nodes/{node_id}", response_model=NodeResponse)
def update_node(
    node_id: int,
    payload: NodeUpdateRequest,
    db: DbSession,
    manager: KnowledgeManager,
    _: CsrfProtected,
) -> NodeResponse:
    node = service.update_node(
        db,
        actor=manager,
        node_id=node_id,
        changes=payload.model_dump(exclude_unset=True),
    )
    return NodeResponse.model_validate(node)


@router.post("/edges", response_model=EdgeResponse, status_code=201)
def create_edge(
    payload: EdgeCreateRequest,
    db: DbSession,
    manager: KnowledgeManager,
    _: CsrfProtected,
) -> EdgeResponse:
    edge = service.create_edge(db, actor=manager, values=payload.model_dump())
    return EdgeResponse.model_validate(edge)
