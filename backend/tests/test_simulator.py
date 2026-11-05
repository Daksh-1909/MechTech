import json
import random
import threading
from datetime import UTC, datetime

from simulator import simulator
from simulator.config import SimulatorConfig
from simulator.dataset import export_csv, export_metadata, generate_dataset
from simulator.scenarios import Scenario

from app.schemas.sensor import SensorReadingPayload


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_generate_reading_respects_scenario_ranges() -> None:
    config = SimulatorConfig(seed=42, scenario=Scenario.NORMAL)
    rng = random.Random(config.seed)  # noqa: S311
    observed_at = datetime(2026, 1, 1, tzinfo=UTC)

    reading = simulator.generate_reading(config, rng, timestamp=observed_at)

    assert reading is not None
    assert reading["equipment_id"] == "motor-001"
    assert reading["timestamp"] == "2026-01-01T00:00:00Z"
    assert 45.0 <= reading["temperature_c"] <= 60.0
    assert 0.10 <= reading["vibration_value"] <= 0.30
    assert reading["vibration_unit"] == "simulated_index"
    assert reading["quality_status"] == "valid"

    disconnected = simulator.generate_reading(
        SimulatorConfig(scenario=Scenario.SENSOR_DISCONNECTION),
        rng,
    )
    assert disconnected is None


def test_send_readings_uses_batch_endpoint_and_device_header(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _FakeResponse({"created": 2, "duplicates": 0, "readings": []})

    monkeypatch.setattr(simulator, "urlopen", fake_urlopen)
    config = SimulatorConfig(
        backend_url="http://api.example/",
        api_prefix="api/v1",
        api_key="device-secret",
        request_timeout_seconds=3.5,
    )
    readings = [
        {
            "equipment_id": "motor-001",
            "timestamp": "2026-01-01T00:00:00Z",
            "temperature_c": 50.0,
            "vibration_value": 0.2,
        },
        {
            "equipment_id": "motor-001",
            "timestamp": "2026-01-01T00:00:01Z",
            "temperature_c": 51.0,
            "vibration_value": 0.21,
        },
    ]

    result = simulator.send_readings(config, readings)

    request = captured["request"]
    assert result["created"] == 2
    assert request.full_url == "http://api.example/api/v1/readings/batch"
    assert request.get_header("X-device-key") == "device-secret"
    assert request.get_header("Content-type") == "application/json"
    assert captured["timeout"] == 3.5
    assert json.loads(request.data) == {"readings": readings}


def test_single_reading_uses_single_endpoint(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return _FakeResponse({"reading": {"id": 1}, "duplicate": False})

    monkeypatch.setattr(simulator, "urlopen", fake_urlopen)
    config = SimulatorConfig(backend_url="http://api.example")
    reading = {
        "equipment_id": "motor-001",
        "timestamp": "2026-01-01T00:00:00Z",
        "temperature_c": 50.0,
        "vibration_value": 0.2,
    }

    simulator.send_readings(config, [reading])

    request = captured["request"]
    assert request.full_url == "http://api.example/api/v1/readings"
    assert json.loads(request.data) == reading


def test_once_sends_one_batch() -> None:
    sent = []

    def fake_sender(config, readings):
        sent.append((config, readings))
        return {}

    config = SimulatorConfig(once=True, batch_size=3, seed=7)
    count = simulator.run_simulation(config, sender=fake_sender)

    assert count == 3
    assert len(sent) == 1
    assert len(sent[0][1]) == 3


def test_continuous_simulation_stops_and_flushes_partial_batch() -> None:
    stop_event = threading.Event()
    sent = []

    def fake_sender(config, readings):
        sent.extend(readings)

    def stop_after_first_sample(_seconds):
        stop_event.set()

    config = SimulatorConfig(interval_seconds=0.01, batch_size=3, seed=7)
    count = simulator.run_simulation(
        config,
        sender=fake_sender,
        sleep=stop_after_first_sample,
        stop_event=stop_event,
    )

    assert count == 1
    assert len(sent) == 1


def test_phase3_dataset_is_deterministic_and_has_five_run_labels(tmp_path) -> None:
    first = generate_dataset(samples_per_scenario=4, seed=42)
    second = generate_dataset(samples_per_scenario=4, seed=42)

    assert first == second
    assert len(first) == 20
    assert {row["schema_version"] for row in first} == {"1.0"}
    assert {row["scenario_label"] for row in first} == {
        "normal",
        "excessive_vibration",
        "overheating",
        "bearing_abnormality",
        "combined_abnormality",
    }
    assert len({row["simulation_run_id"] for row in first}) == 5
    assert [row["sequence"] for row in first] == list(range(20))
    assert all(row["vibration_unit"] == "simulated_index" for row in first)
    assert all(SensorReadingPayload.model_validate(row) for row in first)

    csv_path = export_csv(first, tmp_path / "dataset.csv")
    metadata_path = export_metadata(first, csv_path, seed=42)
    assert csv_path.is_file()
    assert metadata_path.is_file()
