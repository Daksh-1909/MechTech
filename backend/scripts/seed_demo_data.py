"""Seed demonstration organization, roles, permissions, demo users, electric motor equipment, components, and sensors."""

import argparse
import sys

from app.db.session import SessionLocal
from app.models import Organization, UserStatus
from app.modules.auth import repository as auth_repo
from app.modules.auth import service as auth_service
from app.modules.equipment import repository as eq_repo
from app.modules.equipment import service as eq_service
from app.modules.monitoring import repository as monitoring_repo
from app.modules.organizations import repository as org_repo
from app.modules.sensors import repository as sensor_repo

DEMO_ORG_NAME = "Academic Demonstration"
DEMO_ORG_SLUG = "academic-demonstration"
DEFAULT_PASSWORD = "demo-password-123"


def seed_demo(db) -> None:
    print("1. Seeding system roles and permissions...")
    roles = auth_repo.ensure_default_roles_and_permissions(db)
    print(f"   Created/verified {len(roles)} roles.")

    print(f"2. Seeding default demo organization: '{DEMO_ORG_NAME}'...")
    demo_org = org_repo.get_organization_by_slug(db, DEMO_ORG_SLUG)
    if not demo_org:
        demo_org = org_repo.create_organization(
            db,
            name=DEMO_ORG_NAME,
            slug=DEMO_ORG_SLUG,
            status="active",
        )
        print(f"   Demo organization created: {demo_org.id}")
    else:
        print(f"   Demo organization already exists: {demo_org.id}")

    print("3. Seeding demonstration users...")
    demo_users = [
        ("Demo Administrator", "demo.admin@example.com", "platform_admin"),
        ("Demo Maintainer", "demo.maintainer@example.com", "maintainer"),
        ("Demo Viewer", "demo.viewer@example.com", "demo_user"),
    ]

    maintainer_user = None
    admin_user = None

    for name, email, role_key in demo_users:
        user = auth_repo.get_user_by_email(db, email)
        if not user:
            user = auth_service.create_user(
                db,
                name=name,
                email=email,
                password=DEFAULT_PASSWORD,
                role=role_key,
                organization_id=demo_org.id if role_key != "platform_admin" else None,
                status=UserStatus.ACTIVE.value,
                commit=False,
            )
            org_repo.add_member(db, organization_id=demo_org.id, user_id=user.id)
            print(f"   Created demo user: {email} ({role_key})")
        else:
            print(f"   Demo user already exists: {email}")

        if email == "demo.maintainer@example.com":
            maintainer_user = user
        elif email == "demo.admin@example.com":
            admin_user = user

    db.flush()

    print("4. Seeding equipment types...")
    eq_types = eq_repo.ensure_default_equipment_types(db)
    motor_type = eq_types["electric_motor"]
    print(f"   Equipment type verified: {motor_type.key}")

    print("5. Seeding sample electric motor...")
    existing_motor = db.query(eq_repo.Equipment).filter_by(organization_id=demo_org.id, asset_tag="DEMO-MTR-001").first()
    if not existing_motor and admin_user:
        motor = eq_repo.create_equipment(
            db,
            organization_id=demo_org.id,
            equipment_type_id=motor_type.id,
            name="Lab Three-Phase Induction Motor",
            created_by=admin_user.id,
            asset_tag="DEMO-MTR-001",
            manufacturer="ABB",
            model_number="M3AA 132 SMB 4",
            serial_number="ABB-DEMO-2026-X1",
            location_label="Academic Lab Bench 1",
            status="operational",
            specification={
                "rated_power_kw": 7.5,
                "rated_voltage_v": 400.0,
                "rated_current_a": 14.8,
                "rated_speed_rpm": 1450.0,
                "frequency_hz": 50.0,
                "phase_count": 3,
                "motor_type": "three_phase_induction",
                "frame_size": "132S",
                "insulation_class": "F",
            },
        )
        print(f"   Demo motor created: {motor.id} ({motor.name})")

        # Seed standard components per architecture specification
        components_spec = [
            ("motor_casing", "Motor Casing & Frame", "housing", "Main cast iron protective housing"),
            ("cooling_fins", "External Cooling Fins", "cooling", "Heat dissipation surface ribs"),
            ("bearing_front", "Drive-End Front Bearing", "bearing", "Front rolling element bearing supporting drive shaft"),
            ("bearing_rear", "Non-Drive-End Rear Bearing", "bearing", "Rear bearing supporting fan end"),
            ("shaft", "Rotational Motor Shaft", "shaft", "Main high-tensile steel transmission shaft"),
            ("rotor", "Squirrel-Cage Rotor", "rotor", "Laminated core squirrel cage rotor assembly"),
            ("stator", "Copper Stator Windings", "stator", "Three-phase insulated copper stator winding assembly"),
            ("cooling_fan", "Bi-directional Cooling Fan", "cooling_fan", "Rear mounted ventilation fan"),
            ("terminal_box", "Power Terminal Box", "terminal_box", "IP66 rated electrical connection terminal box"),
        ]

        component_map = {}
        for key, comp_name, comp_type, desc in components_spec:
            comp = eq_repo.create_component(
                db,
                organization_id=demo_org.id,
                equipment_id=motor.id,
                component_key=key,
                name=comp_name,
                component_type=comp_type,
                description=desc,
            )
            component_map[key] = comp
        print(f"   Created {len(components_spec)} motor components.")

        # Seed standard sensors
        sensors_spec = [
            ("temp_bearing_front", "temperature", "°C", "bearing_front", {"min_range": -20.0, "max_range": 150.0}),
            ("vib_bearing_front", "vibration", "mm/s", "bearing_front", {"min_range": 0.0, "max_range": 25.0, "metric": "rms_velocity"}),
            ("temp_stator", "temperature", "°C", "stator", {"min_range": -20.0, "max_range": 180.0}),
            ("current_phase_a", "current", "A", "stator", {"min_range": 0.0, "max_range": 50.0}),
            ("rotational_speed", "speed", "RPM", "shaft", {"min_range": 0.0, "max_range": 3000.0}),
        ]

        for s_key, m_type, unit, comp_key, cfg in sensors_spec:
            target_comp = component_map.get(comp_key)
            sensor_repo.create_sensor(
                db,
                organization_id=demo_org.id,
                equipment_id=motor.id,
                component_id=target_comp.id if target_comp else None,
                sensor_key=s_key,
                measurement_type=m_type,
                unit=unit,
                configuration=cfg,
            )
        print(f"   Created {len(sensors_spec)} monitoring sensors.")

        # Assign maintainer
        if maintainer_user:
            eq_repo.create_assignment(
                db,
                equipment_id=motor.id,
                user_id=maintainer_user.id,
                assigned_by=admin_user.id,
                assignment_type="primary_maintainer",
            )
            print("   Assigned demo maintainer to sample motor.")

        # Seed standard monitoring rules
        demo_rules = [
            ("Stator Overheat Warning", "temperature", "gt", 75.0, "°C", 0, "high"),
            ("Drive-End Vibration Warning", "vibration", "gt", 0.45, "mm/s", 5, "critical"),
        ]
        for r_name, m_type, op, thresh, unit, dur, sev in demo_rules:
            monitoring_repo.create_rule(
                db,
                organization_id=demo_org.id,
                equipment_type_id=motor_type.id,
                name=r_name,
                measurement_type=m_type,
                operator=op,
                threshold=thresh,
                unit=unit,
                duration_seconds=dur,
                severity=sev,
                created_by=admin_user.id,
            )
        print(f"   Created {len(demo_rules)} default monitoring rules.")
    else:
        print("   Sample motor already exists.")

    db.commit()
    print("Demo seeding completed successfully.")


def main() -> int:
    with SessionLocal() as db:
        try:
            seed_demo(db)
        except Exception as exc:
            print(f"Error seeding demo data: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
