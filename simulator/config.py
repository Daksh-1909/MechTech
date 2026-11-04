from dataclasses import dataclass

from simulator.scenarios import Scenario


@dataclass(slots=True)
class SimulatorConfig:
    equipment_id: str = "motor-001"
    backend_url: str = "http://127.0.0.1:8000"
    interval_seconds: float = 2.0
    scenario: Scenario = Scenario.NORMAL
    seed: int | None = None
    duration_seconds: float | None = None
    source: str = "simulator"
