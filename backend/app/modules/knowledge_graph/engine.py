"""Knowledge Graph reasoning service using NetworkX.

Loads typed nodes and directed edges from the database to perform graph-based
fault localization, symptom tracing, diagnostic procedure retrieval, and
maintenance recommendation reasoning.
"""

from typing import Any
import uuid

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import NodeType, RelationshipType
from app.models.knowledge import KnowledgeEdge, KnowledgeNode


class KnowledgeGraphEngine:
    """In-memory NetworkX directed graph populated from relational database records."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._key_to_id: dict[str, uuid.UUID] = {}
        self._id_to_key: dict[uuid.UUID, str] = {}

    def load_from_db(self, db: Session) -> None:
        """Synchronize the NetworkX graph with current database knowledge nodes and edges."""
        self.graph.clear()
        self._key_to_id.clear()
        self._id_to_key.clear()

        nodes = list(db.scalars(select(KnowledgeNode)))
        for node in nodes:
            self._key_to_id[node.key] = node.id
            self._id_to_key[node.id] = node.key
            self.graph.add_node(
                node.key,
                id=str(node.id),
                node_type=node.node_type,
                label=node.label,
                description=node.description,
                attributes=node.attributes_json or {},
            )

        edges = list(db.scalars(select(KnowledgeEdge)))
        for edge in edges:
            src_key = self._id_to_key.get(edge.source_node_id)
            tgt_key = self._id_to_key.get(edge.target_node_id)
            if src_key and tgt_key:
                self.graph.add_edge(
                    src_key,
                    tgt_key,
                    id=str(edge.id),
                    relationship=edge.relationship_type,
                    weight=float(edge.weight),
                    confidence=float(edge.confidence),
                    description=edge.description,
                    attributes=edge.attributes_json or {},
                )

    def reason_from_symptoms_and_ml(
        self,
        symptom_keys: list[str],
        ml_prediction_class: str | None = None,
    ) -> list[dict[str, Any]]:
        """Reason across graph edges to infer candidate faults, affected components,

        diagnostic check procedures, and repair recommendations.
        """
        candidate_scores: dict[str, float] = {}
        candidate_evidence: dict[str, list[dict[str, Any]]] = {}

        # 1. Traverse INDICATES edges from observed symptoms -> faults
        for sym in symptom_keys:
            if not self.graph.has_node(sym):
                continue
            for _, fault_key, data in self.graph.out_edges(sym, data=True):
                if data.get("relationship") == RelationshipType.INDICATES.value:
                    conf = data.get("confidence", 0.7)
                    weight = data.get("weight", 1.0)
                    score = conf * weight
                    candidate_scores[fault_key] = candidate_scores.get(fault_key, 0.0) + score
                    if fault_key not in candidate_evidence:
                        candidate_evidence[fault_key] = []
                    candidate_evidence[fault_key].append(
                        {
                            "symptom": sym,
                            "symptom_label": self.graph.nodes[sym].get("label", sym),
                            "relationship": "INDICATES",
                            "confidence": conf,
                        }
                    )

        # 2. Boost candidates that align with ML prediction class
        if ml_prediction_class and ml_prediction_class != "normal":
            for fault_key in list(candidate_scores.keys()):
                # Check for label similarity or explicit mapping
                if ml_prediction_class.lower() in fault_key.lower():
                    candidate_scores[fault_key] += 1.2
                    candidate_evidence[fault_key].append(
                        {
                            "source": "ml_prediction_alignment",
                            "predicted_class": ml_prediction_class,
                            "boost": 1.2,
                        }
                    )

        # Sort candidate faults by score descending
        sorted_faults = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

        results: list[dict[str, Any]] = []
        for fault_key, score in sorted_faults:
            fault_node = self.graph.nodes.get(fault_key, {})
            affected_components: list[dict[str, str]] = []
            diagnostic_steps: list[dict[str, str]] = []
            repair_actions: list[dict[str, str]] = []
            root_causes: list[dict[str, str]] = []

            # Outgoing edges from fault
            for _, target_key, edge_data in self.graph.out_edges(fault_key, data=True):
                rel = edge_data.get("relationship")
                target_node = self.graph.nodes.get(target_key, {})
                label = target_node.get("label", target_key)
                desc = target_node.get("description")

                if rel == RelationshipType.AFFECTS.value:
                    affected_components.append({"key": target_key, "label": label, "description": desc})
                elif rel == RelationshipType.CHECK_WITH.value:
                    diagnostic_steps.append({"key": target_key, "label": label, "description": desc})
                elif rel == RelationshipType.MAY_BE_RESOLVED_BY.value:
                    repair_actions.append({"key": target_key, "label": label, "description": desc})

            # Incoming edges to fault (e.g. MAY_CAUSE)
            for source_key, _, edge_data in self.graph.in_edges(fault_key, data=True):
                rel = edge_data.get("relationship")
                source_node = self.graph.nodes.get(source_key, {})
                if rel == RelationshipType.MAY_CAUSE.value:
                    root_causes.append(
                        {
                            "key": source_key,
                            "label": source_node.get("label", source_key),
                            "description": source_node.get("description"),
                        }
                    )

            results.append(
                {
                    "fault_key": fault_key,
                    "fault_label": fault_node.get("label", fault_key),
                    "fault_description": fault_node.get("description"),
                    "graph_score": round(score, 3),
                    "evidence": candidate_evidence.get(fault_key, []),
                    "affected_components": affected_components,
                    "diagnostic_steps": diagnostic_steps,
                    "repair_actions": repair_actions,
                    "root_causes": root_causes,
                }
            )

        return results

    def get_neighborhood(self, node_key: str, depth: int = 1) -> dict[str, Any]:
        """Return subgraph around a given node up to specified depth."""
        if not self.graph.has_node(node_key):
            return {"nodes": [], "edges": []}

        sub_nodes = set([node_key])
        current_layer = set([node_key])

        for _ in range(depth):
            next_layer = set()
            for n in current_layer:
                next_layer.update(self.graph.successors(n))
                next_layer.update(self.graph.predecessors(n))
            sub_nodes.update(next_layer)
            current_layer = next_layer

        subgraph = self.graph.subgraph(sub_nodes)

        nodes_list = []
        for n in subgraph.nodes:
            d = dict(self.graph.nodes[n])
            d["key"] = n
            nodes_list.append(d)

        edges_list = []
        for u, v, d in subgraph.edges(data=True):
            ed = dict(d)
            ed["source"] = u
            ed["target"] = v
            edges_list.append(ed)

        return {"nodes": nodes_list, "edges": edges_list}

