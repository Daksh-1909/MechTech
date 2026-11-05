from dataclasses import dataclass

from simulator.scenarios import Scenario


@dataclass(slots=True)
class SimulatorConfig:
    equipment_id: str = "motor-001"
    backend_url: str = "http://127.0.0.1:8000"
    api_prefix: str = "/api/v1"
    interval_seconds: float = 2.0
    scenario: Scenario = Scenario.NORMAL
    seed: int | None = None
    duration_seconds: float | None = None
    source: str = "simulator"
    api_key: str | None = None
    batch_size: int = 1
    once: bool = False
    request_timeout_seconds: float = 5.0
    max_retries: int = 3

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero.")
        if not 1 <= self.batch_size <= 100:
            raise ValueError("batch_size must be between 1 and 100.")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be greater than zero.")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least one.")
