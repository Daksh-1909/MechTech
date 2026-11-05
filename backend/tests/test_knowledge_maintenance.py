from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.main import app
from app.models import Alert, UserRole
from app.models.enums import EquipmentStatus
from app.modules.knowledge_graph import service as graph_service
from tests.helpers import create_user, csrf_headers, iso, login, make_equipment


def test_knowledge_graph_persists_traverses_and_enforces_admin_write(
    client: TestClient,
    db_session,
) -> None:
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    operator = create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    csrf = login(client, admin.email)
    prefix = settings.api_v1_prefix

    symptom = client.post(
        f"{prefix}/knowledge-graph/nodes",
        json={
            "node_type": "symptom",
            "stable_key": "symptom:high_vibration",
            "label": "High vibration",
            "attributes_json": {"severity": "prototype"},
        },
        headers=csrf_headers(csrf),
    )
    assert symptom.status_code == 201, symptom.text
    symptom_id = symptom.json()["id"]

    fault = client.post(
        f"{prefix}/knowledge-graph/nodes",
        json={
            "node_type": "fault",
            "stable_key": "fault:bearing_wear",
            "label": "Bearing wear",
        },
        headers=csrf_headers(csrf),
    )
    assert fault.status_code == 201
    fault_id = fault.json()["id"]

    action = client.post(
        f"{prefix}/knowledge-graph/nodes",
        json={
            "node_type": "repair_action",
            "stable_key": "repair:replace_bearing",
            "label": "Replace bearing",
        },
        headers=csrf_headers(csrf),
    )
    assert action.status_code == 201
    action_id = action.json()["id"]

    duplicate = client.post(
        f"{prefix}/knowledge-graph/nodes",
        json={
            "node_type": "symptom",
            "stable_key": "symptom:high_vibration",
            "label": "Duplicate",
        },
        headers=csrf_headers(csrf),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "NODE_EXISTS"

    updated = client.patch(
        f"{prefix}/knowledge-graph/nodes/{symptom_id}",
        json={"label": "Elevated vibration"},
        headers=csrf_headers(csrf),
    )
    assert updated.status_code == 200
    assert updated.json()["label"] == "Elevated vibration"

    first_edge = client.post(
        f"{prefix}/knowledge-graph/edges",
        json={
            "source_node_id": symptom_id,
            "target_node_id": fault_id,
            "relationship_type": "INDICATES",
        },
        headers=csrf_headers(csrf),
    )
    assert first_edge.status_code == 201, first_edge.text

    second_edge = client.post(
        f"{prefix}/knowledge-graph/edges",
        json={
            "source_node_id": fault_id,
            "target_node_id": action_id,
            "relationship_type": "MAY_BE_RESOLVED_BY",
        },
        headers=csrf_headers(csrf),
    )
    assert second_edge.status_code == 201

    duplicate_edge = client.post(
        f"{prefix}/knowledge-graph/edges",
        json={
            "source_node_id": symptom_id,
            "target_node_id": fault_id,
            "relationship_type": "INDICATES",
        },
        headers=csrf_headers(csrf),
    )
    assert duplicate_edge.status_code == 409

    self_edge = client.post(
        f"{prefix}/knowledge-graph/edges",
        json={
            "source_node_id": symptom_id,
            "target_node_id": symptom_id,
            "relationship_type": "AFFECTS",
        },
        headers=csrf_headers(csrf),
    )
    assert self_edge.status_code == 400

    missing_edge = client.post(
        f"{prefix}/knowledge-graph/edges",
        json={
            "source_node_id": 999999,
            "target_node_id": fault_id,
            "relationship_type": "AFFECTS",
        },
        headers=csrf_headers(csrf),
    )
    assert missing_edge.status_code == 404

    graph = client.get(f"{prefix}/knowledge-graph")
    assert graph.status_code == 200
    assert graph.json()["meta"] == {"node_count": 3, "edge_count": 2}

    near = client.get(
        f"{prefix}/knowledge-graph/nodes/{symptom_id}/neighbors",
        params={"depth": 1},
    )
    assert near.status_code == 200
    assert near.json()["meta"]["total_neighbors"] == 2

    far = client.get(
        f"{prefix}/knowledge-graph/nodes/{symptom_id}/neighbors",
        params={"depth": 2},
    )
    assert far.status_code == 200
    assert far.json()["meta"]["total_neighbors"] == 3

    bounded = client.get(
        f"{prefix}/knowledge-graph/nodes/{symptom_id}/neighbors",
        params={"depth": 2, "limit": 1},
    )
    assert bounded.status_code == 200
    assert len(bounded.json()["nodes"]) == 1

    invalid_depth = client.get(
        f"{prefix}/knowledge-graph/nodes/{symptom_id}/neighbors",
        params={"depth": 4},
    )
    assert invalid_depth.status_code == 422

    with SessionLocal() as fresh_session:
        reconstructed = graph_service.build_graph(fresh_session)
    assert reconstructed.number_of_nodes() == 3
    assert reconstructed.number_of_edges() == 2
    assert reconstructed.has_edge(symptom_id, fault_id)

    with TestClient(app) as operator_client:
        operator_csrf = login(operator_client, operator.email)
        forbidden = operator_client.post(
            f"{prefix}/knowledge-graph/nodes",
            json={
                "node_type": "part",
                "stable_key": "part:bearing",
                "label": "Bearing",
            },
            headers=csrf_headers(operator_csrf),
        )
        assert forbidden.status_code == 403


def test_technician_creates_and_updates_authorized_maintenance_records(
    client: TestClient,
    db_session,
) -> None:
    make_equipment(db_session)
    make_equipment(
        db_session,
        equipment_id="motor-archived",
        status=EquipmentStatus.ARCHIVED,
    )
    alert = Alert(
        equipment_id="motor-001",
        alert_type="high_vibration",
        severity="medium",
        title="High vibration",
        status="open",
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)

    technician = create_user(
        db_session,
        email="tech@example.com",
        role=UserRole.TECHNICIAN,
    )
    other_technician = create_user(
        db_session,
        email="tech2@example.com",
        role=UserRole.TECHNICIAN,
    )
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)
    operator = create_user(db_session, email="operator@example.com", role=UserRole.OPERATOR)
    csrf = login(client, technician.email)
    prefix = settings.api_v1_prefix

    payload = {
        "equipment_id": "motor-001",
        "related_alert_id": alert.id,
        "inspection_timestamp": iso(utcnow()),
        "symptoms": "Vibration above prototype threshold",
        "work_performed": "Inspected bearing",
        "parts_replaced_json": [{"name": "Bearing", "quantity": 1}],
        "outcome": "resolved",
        "verification_status": "pending",
        "notes": "Prototype maintenance record",
    }
    created = client.post(
        f"{prefix}/maintenance-records",
        json=payload,
        headers=csrf_headers(csrf),
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["technician_id"] == technician.id
    assert body["related_alert_id"] == alert.id
    record_id = body["id"]

    invalid_alert = client.post(
        f"{prefix}/maintenance-records",
        json={
            **payload,
            "related_alert_id": 999999,
        },
        headers=csrf_headers(csrf),
    )
    assert invalid_alert.status_code == 400
    assert invalid_alert.json()["error"]["code"] == "INVALID_ALERT_REFERENCE"

    archived = client.post(
        f"{prefix}/maintenance-records",
        json={
            **payload,
            "equipment_id": "motor-archived",
            "related_alert_id": None,
        },
        headers=csrf_headers(csrf),
    )
    assert archived.status_code == 409

    own_update = client.patch(
        f"{prefix}/maintenance-records/{record_id}",
        json={"work_performed": "Replaced bearing", "verification_status": "verified"},
        headers=csrf_headers(csrf),
    )
    assert own_update.status_code == 200
    assert own_update.json()["work_performed"] == "Replaced bearing"

    with TestClient(app) as other_client:
        other_csrf = login(other_client, other_technician.email)
        forbidden_update = other_client.patch(
            f"{prefix}/maintenance-records/{record_id}",
            json={"notes": "Unauthorized edit"},
            headers=csrf_headers(other_csrf),
        )
        assert forbidden_update.status_code == 403

    with TestClient(app) as operator_client:
        operator_csrf = login(operator_client, operator.email)
        forbidden_create = operator_client.post(
            f"{prefix}/maintenance-records",
            json=payload,
            headers=csrf_headers(operator_csrf),
        )
        assert forbidden_create.status_code == 403

    admin_csrf = login(client, admin.email)
    admin_update = client.patch(
        f"{prefix}/maintenance-records/{record_id}",
        json={"notes": "Admin-reviewed record"},
        headers=csrf_headers(admin_csrf),
    )
    assert admin_update.status_code == 200
    assert admin_update.json()["notes"] == "Admin-reviewed record"

    listed = client.get(
        f"{prefix}/maintenance-records",
        params={"equipment_id": "motor-001", "outcome": "resolved"},
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [record_id]

    detail = client.get(f"{prefix}/maintenance-records/{record_id}")
    assert detail.status_code == 200
    assert detail.json()["technician_id"] == technician.id

    missing = client.get(f"{prefix}/maintenance-records/999999")
    assert missing.status_code == 404

    records = list(db_session.scalars(select(Alert)))
    assert len(records) == 1
