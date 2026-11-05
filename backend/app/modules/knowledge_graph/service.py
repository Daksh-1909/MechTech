import networkx as nx
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.time import utcnow
from app.models import KnowledgeEdge, KnowledgeNode, User
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.knowledge_graph import repository

MAX_GRAPH_NODES = 500
MAX_GRAPH_EDGES = 2000
MAX_NEIGHBOR_NODES = 200
MAX_DEPTH = 3


def get_node(db: Session, node_id: int) -> KnowledgeNode:
    node = repository.get_node(db, node_id)
    if node is None:
        raise AppError("Knowledge node not found.", code="NOT_FOUND", status_code=404)
    return node


def build_graph(db: Session) -> nx.DiGraph:
    graph = nx.DiGraph()
    nodes = repository.list_nodes(db, node_type=None, limit=MAX_GRAPH_NODES)
    node_ids = {node.id for node in nodes}

    for node in nodes:
        graph.add_node(
            node.id,
            node_type=node.node_type,
            stable_key=node.stable_key,
            label=node.label,
            description=node.description,
            attributes_json=node.attributes_json,
        )

    edges = repository.list_edges(db, limit=MAX_GRAPH_EDGES)
    for edge in edges:
        if edge.source_node_id in node_ids and edge.target_node_id in node_ids:
            graph.add_edge(
                edge.source_node_id,
                edge.target_node_id,
                edge_id=edge.id,
                relationship_type=edge.relationship_type,
                description=edge.description,
            )
    return graph


def get_graph(
    db: Session,
    *,
    node_type: str | None,
    limit: int,
) -> tuple[list[KnowledgeNode], list[KnowledgeEdge]]:
    nodes = repository.list_nodes(db, node_type=node_type, limit=min(limit, MAX_GRAPH_NODES))
    node_ids = {node.id for node in nodes}
    edges = [
        edge
        for edge in repository.list_edges(db, limit=MAX_GRAPH_EDGES)
        if edge.source_node_id in node_ids and edge.target_node_id in node_ids
    ]
    return nodes, edges


def get_neighbors(
    db: Session,
    *,
    node_id: int,
    depth: int,
    limit: int,
) -> tuple[list[KnowledgeNode], list[KnowledgeEdge], int]:
    get_node(db, node_id)
    depth = max(1, min(depth, MAX_DEPTH))
    limit = max(1, min(limit, MAX_NEIGHBOR_NODES))

    graph = build_graph(db)
    if node_id not in graph:
        raise AppError("Knowledge node not found.", code="NOT_FOUND", status_code=404)

    subgraph = nx.ego_graph(graph, node_id, radius=depth, undirected=True)
    selected_ids = list(subgraph.nodes)[:limit]

    nodes = [repository.get_node(db, item) for item in selected_ids]
    present_nodes = [node for node in nodes if node is not None]

    edges: list[KnowledgeEdge] = []
    for edge in repository.list_edges(db, limit=MAX_GRAPH_EDGES):
        if edge.source_node_id in selected_ids and edge.target_node_id in selected_ids:
            edges.append(edge)

    return present_nodes, edges, len(subgraph.nodes)


def create_node(
    db: Session,
    *,
    actor: User,
    values: dict,
) -> KnowledgeNode:
    stable_key = str(values["stable_key"]).strip()
    if repository.get_node_by_stable_key(db, stable_key) is not None:
        raise AppError(
            "A knowledge node with this stable key already exists.",
            code="NODE_EXISTS",
            status_code=409,
        )

    values["stable_key"] = stable_key
    values["node_type"] = values["node_type"].value
    node = KnowledgeNode(**values)
    db.add(node)
    db.flush()
    audit_service.record_event(
        db,
        action=AuditAction.KNOWLEDGE_NODE_CREATED,
        resource_type="knowledge_node",
        resource_id=node.id,
        actor_user_id=actor.id,
        metadata={"stable_key": stable_key, "node_type": node.node_type},
    )
    db.commit()
    db.refresh(node)
    return node


def update_node(
    db: Session,
    *,
    actor: User,
    node_id: int,
    changes: dict,
) -> KnowledgeNode:
    node = get_node(db, node_id)
    allowed_fields = {"label", "description", "attributes_json"}
    updated_fields = [field for field in changes if field in allowed_fields]
    for field in updated_fields:
        setattr(node, field, changes[field])

    if updated_fields:
        node.updated_at = utcnow()
        audit_service.record_event(
            db,
            action=AuditAction.KNOWLEDGE_NODE_UPDATED,
            resource_type="knowledge_node",
            resource_id=node.id,
            actor_user_id=actor.id,
            metadata={"fields": updated_fields},
        )
        db.commit()
        db.refresh(node)
    return node


def create_edge(
    db: Session,
    *,
    actor: User,
    values: dict,
) -> KnowledgeEdge:
    source_node_id = values["source_node_id"]
    target_node_id = values["target_node_id"]
    if source_node_id == target_node_id:
        raise AppError(
            "Self-referencing knowledge edges are not allowed.",
            code="INVALID_EDGE",
            status_code=400,
        )

    get_node(db, source_node_id)
    get_node(db, target_node_id)

    relationship_type = values["relationship_type"].value
    if (
        repository.get_edge_between(
            db,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
        )
        is not None
    ):
        raise AppError(
            "This relationship already exists.",
            code="EDGE_EXISTS",
            status_code=409,
        )

    values["relationship_type"] = relationship_type
    edge = KnowledgeEdge(**values)
    db.add(edge)
    db.flush()
    audit_service.record_event(
        db,
        action=AuditAction.KNOWLEDGE_EDGE_CREATED,
        resource_type="knowledge_edge",
        resource_id=edge.id,
        actor_user_id=actor.id,
        metadata={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "relationship_type": relationship_type,
        },
    )
    db.commit()
    db.refresh(edge)
    return edge
