import json
import logging
import sqlite3

from app.core.config import settings
from app.core.logging import JsonFormatter
from app.ml.datasets import SYNTHETIC_LABELS, generate_synthetic_window_dataset
from app.models import UserRole
from scripts.backup_restore import backup_database, restore_database, verify_database
from scripts.benchmark import percentile, summarize
from scripts.evaluate_model import evaluate_artifact
from scripts.seed_knowledge_graph import seed
from scripts.train_anomaly_model import train_model
from tests.helpers import create_user


def test_synthetic_dataset_is_deterministic_and_balanced() -> None:
    first = generate_synthetic_window_dataset(samples=20, seed=7, window_size=5)
    second = generate_synthetic_window_dataset(samples=20, seed=7, window_size=5)
    features, labels, feature_names = first

    assert first == second
    assert len(features) == 20
    assert len(features[0]) == len(feature_names)
    assert set(labels) == set(SYNTHETIC_LABELS)
    assert all(labels.count(label) == 4 for label in SYNTHETIC_LABELS)


def test_training_and_evaluation_scripts_produce_artifacts() -> None:
    output = settings.data_root / "models" / "classification" / "test-tool.joblib"

    metrics_path, metrics = train_model(
        samples=40,
        window_size=4,
        seed=3,
        output=output,
    )

    assert output.is_file()
    assert metrics_path.is_file()
    assert metrics["accuracy"] > 0.25
    assert metrics["test_samples"] > 0
    assert metrics["run_sets_disjoint"] is True

    evaluation = evaluate_artifact(output, samples=20, window_size=4, seed=11)
    assert evaluation["accuracy"] > 0.25
    assert evaluation["labels"] == list(SYNTHETIC_LABELS)


def test_seed_knowledge_graph_is_idempotent(db_session) -> None:
    admin = create_user(db_session, email="admin@example.com", role=UserRole.ADMIN)

    first = seed(admin_email=admin.email)
    second = seed(admin_email=admin.email)

    assert first[0] > 0
    assert first[2] > 0
    assert second[0] == 0
    assert second[2] == 0
    assert second[1] == first[0]
    assert second[3] == first[2]


def test_backup_restore_round_trip(tmp_path) -> None:
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO sample (value) VALUES ('alpha')")

    backup = tmp_path / "backup.db"
    report = backup_database(source, backup)
    assert report["integrity_check"] == "ok"
    assert verify_database(backup) == "ok"

    target = tmp_path / "restored.db"
    target.write_bytes(b"old")
    restore_database(backup, target, force=True)

    with sqlite3.connect(target) as connection:
        values = [row[0] for row in connection.execute("SELECT value FROM sample")]
    assert values == ["alpha"]


def test_benchmark_percentiles_use_nearest_rank() -> None:
    values = [float(value) for value in range(1, 101)]

    assert percentile(values, 50) == 50.0
    assert percentile(values, 95) == 95.0
    assert percentile(values, 99) == 99.0
    assert summarize(values)["count"] == 100


def test_structured_logs_redact_sensitive_values() -> None:
    record = logging.LogRecord(
        name="mechtech.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request password=super-secret token: abc authorization: Bearer xyz",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["request_id"] == "request-123"
    assert payload["level"] == "INFO"
    assert "super-secret" not in payload["message"]
    assert "abc" not in payload["message"]
    assert "xyz" not in payload["message"]
    assert "[redacted]" in payload["message"]
