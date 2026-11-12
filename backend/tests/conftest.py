import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_TEST_ROOT = tempfile.mkdtemp(prefix="mechtech-tests-")
_TEST_DB_DIR = Path(_TEST_ROOT) / "db"
_TEST_DATA_DIR = Path(_TEST_ROOT) / "data"
_TEST_DB_DIR.mkdir(parents=True, exist_ok=True)
_TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DB_DIR / 'test.db').as_posix()}"
os.environ["DATA_ROOT"] = str(_TEST_DATA_DIR)

_BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    from alembic.config import Config
    from alembic import command
    from app.db.base import Base
    from app.db.session import engine

    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_DIR / "alembic"))
    try:
        command.upgrade(config, "head")
    except Exception:
        # Fallback to create_all for test environment if head is not initialized
        Base.metadata.create_all(engine)

    # Ensure all newly added tables are also created
    Base.metadata.create_all(engine)


@pytest.fixture
def client() -> Generator[TestClient]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session() -> Generator[Session]:
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def db(db_session: Session) -> Session:
    return db_session


@pytest.fixture(autouse=True)
def _clean_tables() -> Generator[None]:
    yield

    from app.db.session import SessionLocal
    from app.models import (
        Alert,
        AnomalyEvent,
        AuditLog,
        Component,
        Diagnosis,
        DiagnosisEvidence,
        Equipment,
        EquipmentAssignment,
        EquipmentSpecification,
        EquipmentType,
        Fault,
        KnowledgeEdge,
        KnowledgeNode,
        MaintenanceRecord,
        MLModel,
        MLPrediction,
        MLTrainingJob,
        ModelRegistry,
        MonitoringRule,
        Organization,
        OrganizationMember,
        PermissionModel,
        RegistrationRequest,
        Role,
        RolePermission,
        Sensor,
        SensorReading,
        User,
        UserRoleAssignment,
        UserSession,
    )

    with SessionLocal() as session:
        for model in (
            RegistrationRequest,
            UserRoleAssignment,
            RolePermission,
            OrganizationMember,
            KnowledgeEdge,
            KnowledgeNode,
            MLPrediction,
            MLTrainingJob,
            MaintenanceRecord,
            DiagnosisEvidence,
            Diagnosis,
            Alert,
            AnomalyEvent,
            MonitoringRule,
            SensorReading,
            Sensor,
            Component,
            EquipmentAssignment,
            EquipmentSpecification,
            Equipment,
            Fault,
            EquipmentType,
            MLModel,
            ModelRegistry,
            AuditLog,
            UserSession,
            User,
            Role,
            PermissionModel,
            Organization,
        ):
            try:
                session.query(model).delete()
            except Exception:
                session.rollback()
        session.commit()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_database() -> Generator[None]:
    yield
    from app.db.session import engine

    engine.dispose()
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)
