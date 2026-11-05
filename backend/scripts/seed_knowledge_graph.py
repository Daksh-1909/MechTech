"""Seed idempotent prototype reference knowledge into SQLite."""

import argparse
import sys

from app.db.session import SessionLocal
from app.models import UserRole
from app.models.enums import NodeType, RelationshipType
from app.modules.auth import repository as auth_repository
from app.modules.auth.service import normalize_email
from app.modules.knowledge_graph import repository, service

NODES: tuple[tuple[str, NodeType, str, str], ...] = (
    (
        "equipment:motor",
        NodeType.EQUIPMENT,
        "Prototype electric motor",
        "Reference node for the simulated motor.",
    ),
    (
        "component:drive_bearing",
        NodeType.COMPONENT,
        "Drive-end bearing",
        "Simulated motor component.",
    ),
    (
        "component:cooling_fan",
        NodeType.COMPONENT,
        "Cooling fan",
        "Simulated motor cooling component.",
    ),
    (
        "sensor:vibration",
        NodeType.SENSOR,
        "Vibration sensor",
        "Simulated normalized vibration channel.",
    ),
    (
        "sensor:temperature",
        NodeType.SENSOR,
        "Temperature sensor",
        "Simulated temperature channel.",
    ),
    (
        "symptom:high_vibration",
        NodeType.SYMPTOM,
        "Elevated vibration",
        "Prototype symptom, not a confirmed diagnosis.",
    ),
    (
        "symptom:high_temperature",
        NodeType.SYMPTOM,
        "Elevated temperature",
        "Prototype symptom, not a confirmed diagnosis.",
    ),
    (
        "fault:bearing_wear",
        NodeType.FAULT,
        "Bearing wear",
        "Prototype fault hypothesis.",
    ),
    (
        "fault:overheating",
        NodeType.FAULT,
        "Overheating",
        "Prototype fault hypothesis.",
    ),
    (
        "diagnostic:bearing_inspection",
        NodeType.DIAGNOSTIC_STEP,
        "Inspect bearing",
        "Visual and tactile inspection step.",
    ),
    (
        "repair:replace_bearing",
        NodeType.REPAIR_ACTION,
        "Replace bearing",
        "Prototype repair action.",
    ),
    (
        "part:bearing",
        NodeType.PART,
        "Replacement bearing",
        "Prototype spare part.",
    ),
)

EDGES: tuple[tuple[str, str, RelationshipType], ...] = (
    ("equipment:motor", "component:drive_bearing", RelationshipType.HAS_COMPONENT),
    ("equipment:motor", "component:cooling_fan", RelationshipType.HAS_COMPONENT),
    ("equipment:motor", "sensor:vibration", RelationshipType.HAS_SENSOR),
    ("equipment:motor", "sensor:temperature", RelationshipType.HAS_SENSOR),
    ("sensor:vibration", "symptom:high_vibration", RelationshipType.MONITORS),
    ("sensor:temperature", "symptom:high_temperature", RelationshipType.MONITORS),
    ("symptom:high_vibration", "fault:bearing_wear", RelationshipType.INDICATES),
    ("symptom:high_temperature", "fault:overheating", RelationshipType.INDICATES),
    ("fault:bearing_wear", "diagnostic:bearing_inspection", RelationshipType.CHECK_WITH),
    ("fault:bearing_wear", "repair:replace_bearing", RelationshipType.MAY_BE_RESOLVED_BY),
    ("repair:replace_bearing", "part:bearing", RelationshipType.REQUIRES_PART),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed prototype knowledge graph nodes and edges.")
    parser.add_argument("--admin-email", required=True)
    return parser


def seed(*, admin_email: str) -> tuple[int, int, int, int]:
    with SessionLocal() as db:
        admin = auth_repository.get_user_by_email(db, normalize_email(admin_email))
        if admin is None or admin.role != UserRole.ADMIN.value or not admin.is_active:
            raise ValueError("An active administrator with that email was not found.")

        nodes_by_key = {}
        created_nodes = 0
        skipped_nodes = 0
        for stable_key, node_type, label, description in NODES:
            node = repository.get_node_by_stable_key(db, stable_key)
            if node is None:
                node = service.create_node(
                    db,
                    actor=admin,
                    values={
                        "node_type": node_type,
                        "stable_key": stable_key,
                        "label": label,
                        "description": description,
                        "attributes_json": {"prototype": True},
                    },
                )
                created_nodes += 1
            else:
                skipped_nodes += 1
            nodes_by_key[stable_key] = node

        existing_edges = {
            (edge.source_node_id, edge.target_node_id, edge.relationship_type)
            for edge in repository.list_edges(db, limit=service.MAX_GRAPH_EDGES)
        }
        created_edges = 0
        skipped_edges = 0
        for source_key, target_key, relationship_type in EDGES:
            source = nodes_by_key[source_key]
            target = nodes_by_key[target_key]
            edge_key = (source.id, target.id, relationship_type.value)
            if edge_key in existing_edges:
                skipped_edges += 1
                continue
            service.create_edge(
                db,
                actor=admin,
                values={
                    "source_node_id": source.id,
                    "target_node_id": target.id,
                    "relationship_type": relationship_type,
                    "description": "Prototype reference relationship.",
                    "attributes_json": {"prototype": True},
                },
            )
            existing_edges.add(edge_key)
            created_edges += 1

    return created_nodes, skipped_nodes, created_edges, skipped_edges


def main() -> int:
    args = build_parser().parse_args()
    try:
        created_nodes, skipped_nodes, created_edges, skipped_edges = seed(
            admin_email=args.admin_email
        )
    except (ValueError, OSError) as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1

    print(f"Nodes created: {created_nodes}, skipped: {skipped_nodes}")
    print(f"Edges created: {created_edges}, skipped: {skipped_edges}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
