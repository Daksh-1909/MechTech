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


def ensure_default_motor_knowledge_graph(db: Session) -> None:
    """Seed baseline knowledge graph nodes and edges for electric motor diagnostics."""
    from sqlalchemy import select
    from app.models.enums import NodeType, RelationshipType

    existing = db.scalar(select(KnowledgeNode).limit(1))
    if existing:
        return

    # Define standard nodes: (key, node_type, label, description)
    nodes_def = [
        # Symptoms
        ("sym_high_temperature", NodeType.SYMPTOM.value, "High Motor Temperature", "Elevated frame or winding thermal readings exceeding threshold."),
        ("sym_high_vibration", NodeType.SYMPTOM.value, "High Overall Vibration", "Excessive RMS or peak vibration velocity."),
        ("sym_speed_drop", NodeType.SYMPTOM.value, "Rotational Speed Drop", "Motor running below rated speed under moderate load."),
        # Faults
        ("fault_bearing_wear", NodeType.FAULT.value, "Drive-End Bearing Degradation", "Flaking, spalling, or micro-pitting in rolling element bearings."),
        ("fault_stator_overheat", NodeType.FAULT.value, "Stator Thermal Overload", "Inter-turn insulation thermal degradation in stator copper windings."),
        ("fault_cooling_failure", NodeType.FAULT.value, "Cooling System Airflow Obstruction", "Clogged ventilation ribs or damaged bi-directional fan assembly."),
        ("fault_rotor_imbalance", NodeType.FAULT.value, "Rotor Dynamic Imbalance", "Mass eccentricity generating 1X rotational speed vibration."),
        # Components
        ("comp_bearing_front", NodeType.COMPONENT.value, "Drive-End Front Bearing", "Front rolling element bearing supporting drive shaft."),
        ("comp_stator_winding", NodeType.COMPONENT.value, "Copper Stator Windings", "Three-phase insulated copper stator winding assembly."),
        ("comp_cooling_fan", NodeType.COMPONENT.value, "Bi-directional Cooling Fan", "Rear mounted ventilation fan."),
        # Diagnostic Steps
        ("step_vibration_fft", NodeType.DIAGNOSTIC_STEP.value, "Vibration Spectrum Analysis", "FFT spectrum analysis focusing on bearing defect frequencies (BPFO, BPFI)."),
        ("step_thermal_imaging", NodeType.DIAGNOSTIC_STEP.value, "Infrared Thermography Scan", "Thermal camera scan to isolate localized hotspot vs uniform frame heating."),
        ("step_bearing_grease_inspection", NodeType.DIAGNOSTIC_STEP.value, "Lubricant Condition Inspection", "Visual and viscosity check for grease discoloration or metal particulate."),
        # Repair Actions
        ("repair_relubricate", NodeType.REPAIR_ACTION.value, "Bearing Lubrication Service", "Purge degraded lubricant and replenish with manufacturer-specified grease."),
        ("repair_replace_bearing", NodeType.REPAIR_ACTION.value, "Bearing Assembly Replacement", "Extract worn bearing and press-fit replacement with calibrated clearance."),
        ("repair_clean_cooling", NodeType.REPAIR_ACTION.value, "Cooling System Maintenance", "Clean ventilation ribs, blow out airflow duct, and inspect fan blades."),
    ]

    nodes_map: dict[str, KnowledgeNode] = {}
    for key, n_type, label, desc in nodes_def:
        node = KnowledgeNode(
            key=key,
            node_type=n_type,
            label=label,
            description=desc,
            version=1,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(node)
        nodes_map[key] = node
    db.flush()

    # Define standard relationships: (src_key, tgt_key, rel_type, weight, confidence)
    edges_def = [
        # Symptoms -> Faults
        ("sym_high_temperature", "fault_stator_overheat", RelationshipType.INDICATES.value, 1.0, 0.90),
        ("sym_high_temperature", "fault_cooling_failure", RelationshipType.INDICATES.value, 0.8, 0.75),
        ("sym_high_vibration", "fault_bearing_wear", RelationshipType.INDICATES.value, 1.0, 0.92),
        ("sym_high_vibration", "fault_rotor_imbalance", RelationshipType.INDICATES.value, 0.7, 0.65),
        # Faults -> Components
        ("fault_bearing_wear", "comp_bearing_front", RelationshipType.AFFECTS.value, 1.0, 0.95),
        ("fault_stator_overheat", "comp_stator_winding", RelationshipType.AFFECTS.value, 1.0, 0.95),
        ("fault_cooling_failure", "comp_cooling_fan", RelationshipType.AFFECTS.value, 1.0, 0.90),
        # Faults -> Diagnostic Procedures
        ("fault_bearing_wear", "step_vibration_fft", RelationshipType.CHECK_WITH.value, 1.0, 0.90),
        ("fault_bearing_wear", "step_bearing_grease_inspection", RelationshipType.CHECK_WITH.value, 0.9, 0.85),
        ("fault_stator_overheat", "step_thermal_imaging", RelationshipType.CHECK_WITH.value, 1.0, 0.90),
        # Faults -> Repair Recommendations
        ("fault_bearing_wear", "repair_relubricate", RelationshipType.MAY_BE_RESOLVED_BY.value, 0.8, 0.75),
        ("fault_bearing_wear", "repair_replace_bearing", RelationshipType.MAY_BE_RESOLVED_BY.value, 1.0, 0.90),
        ("fault_cooling_failure", "repair_clean_cooling", RelationshipType.MAY_BE_RESOLVED_BY.value, 1.0, 0.90),
    ]

    for src_key, tgt_key, rel, wt, conf in edges_def:
        src = nodes_map.get(src_key)
        tgt = nodes_map.get(tgt_key)
        if src and tgt:
            edge = KnowledgeEdge(
                source_node_id=src.id,
                target_node_id=tgt.id,
                relationship_type=rel,
                weight=wt,
                confidence=conf,
                version=1,
                created_at=utcnow(),
            )
            db.add(edge)
    db.commit()

