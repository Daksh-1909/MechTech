from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KnowledgeEdge, KnowledgeNode


def get_node(db: Session, node_id: int) -> KnowledgeNode | None:
    return db.get(KnowledgeNode, node_id)


def get_node_by_stable_key(db: Session, stable_key: str) -> KnowledgeNode | None:
    return db.scalar(select(KnowledgeNode).where(KnowledgeNode.stable_key == stable_key))


def list_nodes(
    db: Session,
    *,
    node_type: str | None,
    limit: int,
) -> list[KnowledgeNode]:
    statement = select(KnowledgeNode)
    if node_type is not None:
        statement = statement.where(KnowledgeNode.node_type == node_type)
    statement = statement.order_by(KnowledgeNode.id.asc()).limit(limit)
    return list(db.scalars(statement))


def list_edges(db: Session, *, limit: int) -> list[KnowledgeEdge]:
    return list(db.scalars(select(KnowledgeEdge).order_by(KnowledgeEdge.id.asc()).limit(limit)))


def get_edge_between(
    db: Session,
    *,
    source_node_id: int,
    target_node_id: int,
    relationship_type: str,
) -> KnowledgeEdge | None:
    return db.scalar(
        select(KnowledgeEdge).where(
            KnowledgeEdge.source_node_id == source_node_id,
            KnowledgeEdge.target_node_id == target_node_id,
            KnowledgeEdge.relationship_type == relationship_type,
        )
    )


def list_edges_for_node(db: Session, node_id: int) -> list[KnowledgeEdge]:
    return list(
        db.scalars(
            select(KnowledgeEdge).where(
                (KnowledgeEdge.source_node_id == node_id)
                | (KnowledgeEdge.target_node_id == node_id)
            )
        )
    )
